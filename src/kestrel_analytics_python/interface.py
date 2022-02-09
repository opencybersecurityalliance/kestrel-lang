"""Python analytics interface executes Python function as Kestrel analytics.

An analytics using this interface should follow the rules:

- The analytics is a Python function

- The function takes in one or more Kestrel variable dumps in Pandas dataframes

- The function returns the same amount of updated Kestrel variable dumps in
  Pandas dataframe, plus a Kestrel display object if any.

- Any parameters in the APPLY command will be passed in as environment varibles

Put your profiles in the python analytics interface config file (YAML):

- Default path: ``~/.config/kestrel/pythonanalytics.yaml``.
- A customized path specified in the environment variable ``KESTREL_PYTHON_ANALYTICS_CONFIG``.

Example of stix-shifter interface config file containing profiles:

.. code-block:: yaml

    profiles:
        # the analytics name to use in the APPLY command
        analytics-name-1:
            # the module to import
            module: /home/user/kestrel-analytics/analytics/piniponmap/analytics.py
            # the analytics function in the module to call
            func: analytics # this will be called to execute analytics
        analytics-name-2:
            module: /home/user/kestrel-analytics/analytics/suspiciousscoring/analytics.py
            func: analytics

"""

import sys
import pathlib
import logging
import inspect
import subprocess
from pandas import DataFrame
from importlib.util import spec_from_file_location, module_from_spec
from contextlib import AbstractContextManager

from kestrel.codegen.display import AbstractDisplay
from kestrel.analytics import AbstractAnalyticsInterface
from kestrel.exceptions import (
    InvalidAnalytics,
    AnalyticsManagerInternalError,
    InvalidAnalyticsInterfaceImplementation,
    AnalyticsError,
    InvalidAnalyticsArgumentCount,
)
from kestrel_analytics_python.config import (
    load_profiles,
)

_logger = logging.getLogger(__name__)


class PythonInterface(AbstractAnalyticsInterface):
    @staticmethod
    def schemes():
        """Python analytics interface only supports ``python://`` scheme."""
        return ["python"]

    @staticmethod
    def list_analytics(config):
        """Load config to list avaliable analytics."""
        if not config:
            config["profiles"] = load_profiles()
        analytics = list(config["profiles"].keys())
        analytics.sort()
        return analytics

    @staticmethod
    def execute(uri, argument_variables, config, session_id=None, parameters=None):
        """Execute an analytics."""
        scheme, _, profile = uri.rpartition("://")

        if not config:
            config["profiles"] = load_profiles()

        if scheme != "python":
            raise AnalyticsManagerInternalError(
                f"interface {__package__} should not process scheme {scheme}"
            )

        with PythonAnalytics(profile, config["profiles"]) as f:
            f.execute(argument_variables)


class PythonAnalytics(AbstractContextManager):
    """Handler of a Python Analytics

    #. Validate and retrieve profile data. The data should be a dict with "module"
    and "func", plus appropriate values.

    #. Prepare the analytics by loading the module. Also verify the function
    exists.

    #. Execute the analytics and process return intelligently.

    #. Clean the environment, especially additional sys.path required by the analytics.

    Args:
        profile_name (str): The name of the profile/analytics.
        profiles (dict): name to profile (dict) mapping.
    """

    def __init__(self, profile_name, profiles):
        self.name = profile_name
        module_name, func_name = get_profile(profile_name, profiles)
        self.module_path = pathlib.Path(module_name).expanduser().resolve()
        self.analytics_function = self._locate_analytics_func(
            self._load_module(), func_name
        )

    def execute(self, arg_variables):
        """Execute the analytics

        Args:
            arg_variables ([VarStruct]): input variables to the analytics.

        Returns:
            - Explicit: a Kestrel Display object.
            - Implicit (side effect): updating the session with returned Kestrel variables
        """
        input_dataframes = [DataFrame(v.get_entities()) for v in arg_variables]
        if len(input_dataframes) != self._get_var_count():
            raise InvalidAnalyticsArgumentCount(
                profile, len(input_dataframes), self._get_var_count()
            )
        else:
            outputs = self.analytics_function(input_dataframes)
            if not isinstance(outputs, tuple):
                outputs = (outputs,)

            output_dfs, output_dsps = [], []
            for x in outputs:
                if isinstance(outputs, DataFrame):
                    output_dfs.append(x)
                elif isinstance(outputs, AbstractDisplay):
                    output_dsps.append(x)
                else:
                    raise AnalyticsError(
                        f'analytics "{self.name}" yielded invalid return: neither DataFrame nor Kestrel Display object'
                    )

            if not outputs:
                raise AnalyticsError(f'analytics "{self.name}" yield nothing')
            if len(output_dsps) > 1:
                raise AnalyticsError(
                    f'analytics "{self.name}" yielded more than one Kestrel Display object'
                )
            if output_dfs and len(output_dfs) != len(input_dataframes):
                raise AnalyticsError(
                    f'analytics "{self.name}" yielded less/more Kestrel variable(s) than given'
                )

            for v, odf in zip(arg_variables, output_dfs):
                if not "id" in odf:
                    raise AnalyticsError(
                        f'analytics "{self.name}" yielded invalid return without "id"'
                    )
                if not "type" in odf:
                    raise AnalyticsError(
                        f'analytics "{self.name}" yielded invalid return without "type"'
                    )

                o_type_set = set(odf["type"])
                o_type = o_type_set.pop()
                if o_type_set:
                    raise AnalyticsError(
                        f'analytics "{self.name}" yielded invalid return with inconsistent types'
                    )

                o_dict = odf.to_dict(orient="records")
                v.store.reassign(v.entity_table, o_dict)

            display = output_dsps[0] if output_dsps else None
            return display

    def _load_module(self):
        sys.path.append(str(self.module_path.parent))
        spec = spec_from_file_location(
            "kestrel_analytics_python.analytics.{profile_name}", str(self.module_path)
        )
        module = module_from_spec(spec)

        missed_package = "pip"
        while missed_package:
            try:
                spec.loader.exec_module(module)
            except ModuleNotFoundError as e:
                if e.name == missed_package:
                    raise AnalyticsError(
                        f'cannot find dependent package "{missed_package}" to install'
                    )
                else:
                    missed_package = e.name
                    _logger.info(
                        f'install missing dependent package "{missed_package}" for analytics "{self.name}"'
                    )
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", missed_package]
                    )
            else:
                missed_package = None

        return module

    def _locate_analytics_func(self, module, func_name):
        if hasattr(module, func_name):
            return getattr(module, func_name)
        else:
            raise InvalidAnalytics(
                self.name,
                "python",
                f'function "{func_name}" not exist in module: {self.module_path}',
            )

    def _get_var_count(self):
        sig = inspect.signature(self.analytics_function)
        return len(sig.parameters)

    def __exit__(self, exception_type, exception_value, traceback):
        if sys.path[-1] == str(self.module_path.parent):
            sys.path.pop()
        else:
            raise InvalidAnalyticsInterfaceImplementation(
                "strange: analytics module directory not found on path."
            )
