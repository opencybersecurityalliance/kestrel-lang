"""Python analytics interface executes Python function as Kestrel analytics.

Use a Python Analytics
----------------------

Create a profile for each analytics in the python analytics interface config
file (YAML):

- Default path: ``~/.config/kestrel/pythonanalytics.yaml``.
- A customized path specified in the environment variable ``KESTREL_PYTHON_ANALYTICS_CONFIG``.

Example of the python analytics interface config file:

.. code-block:: yaml

    profiles:
        analytics-name-1: # the analytics name to use in the APPLY command
            module: /home/user/kestrel-analytics/analytics/piniponmap/analytics.py
            func: analytics # the analytics function in the module to call
        analytics-name-2:
            module: /home/user/kestrel-analytics/analytics/suspiciousscoring/analytics.py
            func: analytics

Develop a Python Analytics
--------------------------

A Python analytics is a python function that follows the rules:

#. The function takes in one or more Kestrel variable dumps in Pandas DataFrames.

#. The return of the function is a tuple containing either or both:

    - Updated variables. The number of variables can be either 0, e.g.,
      visualization analytics, or the same number as input Kestrel variables.
      The order of the updated variables should follow the same order as input
      variables.

    - An object to display, which can be any of the following types:

        - Kestrel display object

        - HTML element as a string

        - Matplotlib figure (by default, Pandas DataFrame plots use this)

   The display object can be either before or after updated variables. In other
   words, if the input variables are ``var1``, ``var2``, and ``var3``, the
   return of the analytics can be either of the following:

   .. code-block:: python

       # the analytics enriches variables without returning a display object
       return var1_updated, var3_updated, var3_updated

       # this is a visualization analytics and no variable updates
       return display_obj

       # the analytics does both variable updates and visualization
       return var1_updated, var3_updated, var3_updated, display_obj

       # the analytics does both variable updates and visualization
       return display_obj, var1_updated, var3_updated, var3_updated


#. Parameters in the APPLY command are passed in as environment varibles. The
   names of the environment variables are the exact parameter keys given in the
   ``APPLY`` command. For example, the following command

   .. code-block::

       APPLY python://a1 ON var1 WITH XPARAM=src_ref.value, YPARAM=number_observed

   creates environment variables ``$XPARAM`` with value ``src_ref.value`` and
   ``$YPARAM`` with value ``number_observed`` to be used by the analytics
   ``a1``. After the execution of the analytics, the environment variables will
   be roll back to the original state.

#. The Python function could spawn other processes or execute other binaries,
   where the Python function just acts like a wrapper. Check our `domain name
   lookup analytics`_ as an example.

.. _domain name lookup analytics: https://github.com/opencybersecurityalliance/kestrel-analytics/tree/release/analytics/domainnamelookup

"""

import os
import sys
import pathlib
import logging
import inspect
import traceback
from collections.abc import Mapping
from pandas import DataFrame
from importlib.util import spec_from_file_location, module_from_spec
from contextlib import AbstractContextManager

from kestrel.codegen.display import AbstractDisplay, DisplayHtml, DisplayFigure
from kestrel.analytics import AbstractAnalyticsInterface
from kestrel.exceptions import (
    InvalidAnalytics,
    AnalyticsManagerInternalError,
    InvalidAnalyticsInterfaceImplementation,
    AnalyticsError,
    InvalidAnalyticsArgumentCount,
    InvalidAnalyticsOutput,
)
from kestrel_analytics_python.config import (
    get_profile,
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

        with PythonAnalytics(profile, config["profiles"], parameters) as func:
            display = func(argument_variables)

        return display


class PythonAnalytics(AbstractContextManager):
    """Handler of a Python Analytics

    Use it as a context manager:

    .. code-block:: python

        with PythonAnalytics(profile_name, profiles, parameters) as func:
            func(input_kestrel_variables)

    #. Validate and retrieve profile data. The data should be a dict with "module"
       and "func", plus appropriate values.

    #. Prepare the analytics by loading the module. Also verify the function
       exists.

    #. Execute the analytics and process return intelligently.

    #. Clean the environment.

    Args:

        profile_name (str): The name of the profile/analytics.

        profiles (dict): name to profile (dict) mapping.

        parameters (dict): key-value pairs of parameters.

    """

    def __init__(self, profile_name, profiles, parameters):
        self.name = profile_name
        self.parameters = parameters
        self.module_name, self.func_name = get_profile(profile_name, profiles)
        self.module_path = pathlib.Path(self.module_name).expanduser().resolve()
        self.module_path_dir_str = str(self.module_path.parent)

    def __enter__(self):
        # accommodate any other Python modules to load in the dir
        self.syspath = sys.path.copy()
        sys.path.append(self.module_path_dir_str)

        # accommodate any other executables or data to load in the dir
        self.cwd_original = os.getcwd()
        os.chdir(self.module_path_dir_str)

        # passing parameters as environment variables
        self.environ_original = os.environ.copy()
        if self.parameters:
            if isinstance(self.parameters, Mapping):
                _logger.debug(f"setting parameters as env vars: {self.parameters}")
                os.environ.update(self.parameters)
            else:
                raise InvalidAnalyticsInterfaceImplementation(
                    "parameters should be passed in as a Mapping"
                )

        # time to load the analytics function
        self.analytics_function = self._locate_analytics_func(self._load_module())

        return self._execute

    def __exit__(self, exception_type, exception_value, traceback):
        sys.path = self.syspath
        os.chdir(self.cwd_original)
        os.environ = self.environ_original

    def _execute(self, arg_variables):
        """Execute the analytics

        Args:
            arg_variables ([VarStruct]): input variables to the analytics.

        Returns:

            Kestrel Display object: The Display object is the explicit return.
            The function also has side effect to update the session with
            returned Kestrel variables.

        """
        input_dataframes = [DataFrame(v.get_entities()) for v in arg_variables]
        if len(input_dataframes) != self._get_var_count():
            raise InvalidAnalyticsArgumentCount(
                self.name, len(input_dataframes), self._get_var_count()
            )
        else:
            try:
                outputs = self.analytics_function(*input_dataframes)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_traceback)
                )
                raise AnalyticsError(f"{self.name} failed at execution:\n{error}")

            if not isinstance(outputs, tuple):
                outputs = (outputs,)

            output_dfs, output_dsps = [], []
            for x in outputs:
                x_class_str = type(x).__module__ + "." + type(x).__name__
                if isinstance(x, DataFrame):
                    output_dfs.append(x)
                elif isinstance(x, AbstractDisplay):
                    _logger.debug(f'analytics "{self.name}" yielded a display object')
                    output_dsps.append(x)
                elif isinstance(x, str):
                    _logger.info(
                        f'analytics "{self.name}" yielded a string return. treat it as an HTML element.'
                    )
                    output_dsps.append(DisplayHtml(x))
                elif x_class_str == "matplotlib.figure.Figure":
                    _logger.info(f'analytics "{self.name}" yielded a figure.')
                    output_dsps.append(DisplayFigure(x))
                else:
                    raise InvalidAnalyticsOutput(self.name, type(x))

            if not outputs:
                raise AnalyticsError(f'analytics "{self.name}" yield nothing')
            if len(output_dsps) > 1:
                raise AnalyticsError(
                    f'analytics "{self.name}" yielded more than one Kestrel Display object'
                )
            if output_dfs:
                if len(output_dfs) != len(input_dataframes):
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
        spec = spec_from_file_location(
            "kestrel_analytics_python.analytics.{profile_name}", str(self.module_path)
        )

        try:
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
        except ModuleNotFoundError as e:
            raise AnalyticsError(
                f"{self.name} misses dependent library: {e.name}",
                "pip install the corresponding Python package",
            )
        except Exception as e:
            if isinstance(e, AttributeError) and e.args == (
                "'NoneType' object has no attribute 'loader'",
            ):
                raise AnalyticsError(
                    f"{self.name} is not found",
                    "please make sure the Python module and function specified in the profile (configuration) exist",
                )
            else:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_traceback)
                )
                raise AnalyticsError(f"{self.name} failed at importing:\n{error}")

        return module

    def _locate_analytics_func(self, module):
        if hasattr(module, self.func_name):
            return getattr(module, self.func_name)
        else:
            raise InvalidAnalytics(
                self.name,
                "python",
                f'function "{self.func_name}" not exist in module: {self.module_path}',
            )

    def _get_var_count(self):
        sig = inspect.signature(self.analytics_function)
        return len(sig.parameters)
