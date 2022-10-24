"""Docker analytics interface executes Kestrel analytics via docker.

An analytics using this interface should follow the rules:

- The analytics is built into a docker container reachable by the Python ``docker`` package.

- The name of the container should start with ``kestrel-analytics-``.

- The container will be launched with a mounted volumn ``/data/`` for exchanging input/output.

- The input Kestrel variables (all records) are put in ``/data/input/`` as
  ``0.parquet.gz``, ``1.parquet.gz``, ..., in the same order as they are passed
  to the ``APPLY`` command.

- The output (updated variable data) should be yielded by the analytics to
  ``/data/output/`` as ``0.parquet.gz``, ``1.parquet.gz``, ..., in the same
  order of the input variables. If a variable is unchanged, the output parquet
  file of it can be omitted.

- If a display object is yielded, the analytics should write it into
  ``/data/display/``.

"""

import docker
import logging
import pandas

from kestrel.analytics import AbstractAnalyticsInterface
from kestrel.exceptions import (
    InvalidAnalytics,
    AnalyticsManagerInternalError,
    AnalyticsError,
)
from kestrel.utils import mkdtemp
from kestrel_analytics_docker.config import (
    DOCKER_IMAGE_PREFIX,
    VAR_FILE_SUFFIX,
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    DISP_FOLDER,
)
from kestrel.codegen.display import DisplayHtml

_logger = logging.getLogger(__name__)


class DockerInterface(AbstractAnalyticsInterface):
    @staticmethod
    def schemes():
        """Docker analytics interface only supports ``docker://`` scheme."""
        return ["docker"]

    @staticmethod
    def list_analytics(config=None):
        """Check docker for the list of Kestrel analytics."""
        docker_images = docker.from_env().images.list()
        tags = [tag for img in docker_images for tag in img.attrs["RepoTags"]]
        image_names = [tag.split(":")[0] for tag in tags]
        analytics_names = [
            img[len(DOCKER_IMAGE_PREFIX) :]
            for img in image_names
            if img.startswith(DOCKER_IMAGE_PREFIX)
        ]
        _logger.debug(f"Analytics names obtained: {str(analytics_names)}")
        return analytics_names

    @staticmethod
    def execute(uri, argument_variables, config=None, session_id=None, parameters=None):
        """Execute an analytics."""

        scheme, _, analytics_name = uri.rpartition("://")
        container_name = DOCKER_IMAGE_PREFIX + analytics_name

        if scheme != "docker":
            raise AnalyticsManagerInternalError(
                f"interface {__package__} should not process scheme {scheme}"
            )

        shared_dir = mkdtemp().resolve()
        input_dir = shared_dir / INPUT_FOLDER
        input_dir.mkdir()
        output_dir = shared_dir / OUTPUT_FOLDER
        output_dir.mkdir()
        display_dir = shared_dir / DISP_FOLDER
        display_dir.mkdir()

        for index, var in enumerate(argument_variables):
            arg_var_file_name = str(index) + VAR_FILE_SUFFIX
            arg_var_file_path = str(input_dir / arg_var_file_name)
            var.dump_to_file(arg_var_file_path)

        dclient = docker.from_env()
        if not dclient.images.list(container_name):
            raise InvalidAnalytics(
                analytics_name,
                "docker",
                f"{container_name} is not an avaliable docker container.",
            )

        # the execution of the container
        try:
            dclient.containers.run(
                container_name,
                volumes={str(shared_dir): {"bind": "/data", "mode": "rw"}},
                environment=parameters,
            )
        except docker.errors.ContainerError as e:
            error = e.stderr.decode("utf-8")
            _logger.error(error)
            raise AnalyticsError(f"{analytics_name} failed: {error}")

        # process returned/updated variables
        for index, var in enumerate(argument_variables):
            arg_var_file_name = str(index) + VAR_FILE_SUFFIX
            arg_var_file_path = str(output_dir / arg_var_file_name)

            var_data = None
            try:
                var_data = pandas.read_parquet(arg_var_file_path)
            except FileNotFoundError:
                _logger.info(
                    f'analytics "{analytics_name}" has no output file {arg_var_file_name}.'
                )
            except Exception as e:
                raise AnalyticsError(
                    f'{e.__class__.__name__}: analytics "{analytics_name}" yielded invalid return data {arg_var_file_path}.'
                )

            if var_data is None:
                continue

            if not "id" in var_data:
                raise AnalyticsError(
                    f'analytics "{analytics_name}" yielded invalid return {arg_var_file_path} without "id".'
                )

            if not "type" in var_data:
                raise AnalyticsError(
                    f'analytics "{analytics_name}" yielded invalid return {arg_var_file_path} without "type".'
                )

            var_data_type_set = set(var_data["type"])
            var_data_type = var_data_type_set.pop()
            if var_data_type_set:
                raise AnalyticsError(
                    f'analytics "{analytics_name}" yielded invalid return {arg_var_file_path} with inconsistent types'
                )

            var_data_dict = var_data.to_dict(orient="records")
            var.store.reassign(var.entity_table, var_data_dict)

        # process returned display
        disp_files = list(display_dir.iterdir())
        if disp_files:
            disp_file = disp_files.pop()
            if disp_files:
                raise AnalyticsError(
                    f'analytics "{analytics_name}" yielded more than one display files'
                )
            if disp_file.suffix == ".html":
                with open(disp_file, "r") as h:
                    html = h.read()
                    display = DisplayHtml(html)
            else:
                raise NotImplementedError
        else:
            display = None

        return display
