"""A Kestrel session provides an isolated stateful runtime space for a huntflow.

A huntflow is the source code or script of a cyber threat hunt, which can be
developed offline in a text editor or interactively as the hunt goes. A Kestrel
session provides the runtime space for a huntflow that allows execution and
inspection of hunt statements in the huntflow. The :class:`Session` class in this
module supports both non-interactive and interactive execution of huntflows as
well as comprehensive APIs besides execution.

.. highlight:: python

Examples:
    A non-interactive execution of a huntflow::

        from kestrel.session import Session
        with Session() as session:
            open(huntflow_file) as hff:
                huntflow = hff.read()
            session.execute(huntflow)

    An interactive composition and execution of a huntflow::

        from kestrel.session import Session
        with Session() as session:
            try:
                hunt_statement = input(">>> ")
            except EOFError:
                print()
                break
            else:
                output = session.execute(hunt_statement)
                print(output)

    Export Kestrel variable to Python::

        from kestrel.session import Session
        huntflow = ""\"newvar = GET process
                               FROM stixshifter://workstationX
                               WHERE [process:name = 'cmd.exe']""\"
        with Session() as session:
            session.execute(huntflow)
            cmds = session.get_variable("newvar")
        for process in cmds:
            print(process["name"])

"""

import tempfile
import os
import pathlib
import shutil
import uuid
import logging
import re
import toml
import time
import math
from datetime import datetime
from lark import UnexpectedCharacters, UnexpectedToken

from kestrel.exceptions import (
    KestrelSyntaxError,
    NoValidConfiguration,
    InvalidStixPattern,
)
from kestrel.syntax.parser import get_all_input_var_names
from kestrel.syntax.parser import parse
from kestrel.syntax.utils import get_keywords
from kestrel.semantics import *
from kestrel.codegen import commands
from kestrel.codegen.display import DisplayBlockSummary
from kestrel.codegen.summary import gen_variable_summary
from firepit import get_storage
from firepit.exceptions import StixPatternError
from kestrel.utils import set_current_working_directory, config_paths
from kestrel.datasource import DataSourceManager
from kestrel.analytics import AnalyticsManager

_logger = logging.getLogger(__name__)


class Session(object):
    """Kestrel Session class

    A session object needs to be instantiated to create a Kestrel runtime space.
    This is the foundation of multi-user dynamic composition and execution of
    huntflows. A Kestrel session has two important properties:

    - Stateful: a session keeps track of states/effects of statements that have
      been previously executed in this session, e.g., the values of previous
      established Kestrel variables. A session can invoke more than one
      :meth:`execute`, and each :meth:`execute` can process a block of Kestrel code,
      i.e., multiple Kestrel statements.

    - Isolated: each session is established in an isolated space (memory and
      file system):

      - Memory isolation is accomplished by OS process and memory space
        management automatically -- different Kestrel session instances will not
        overlap in memory.

      - File system isolation is accomplished with the setup and management of
        a temporary runtime directory for each session.

    Args:

      runtime_dir (str): to be used for :attr:`runtime_directory`.

      store_path (str): the file path or URL to initialize :attr:`store`.

      debug_mode (bool): to be assign to :attr:`debug_mode`.

    Attributes:

        session_id (str): The Kestrel session ID, which will be created as a random
          UUID if not given in the constructor.

        runtime_directory (str): The runtime directory stores session related
          data in the file system such as local cache of queried results,
          session log, and may be the internal store. The session will use
          a temporary directory derived from :attr:`session_id` if the path is
          not specified in constructor parameters.

        store (firepit.SqlStorage): The internal store used
          by the session to normalize queried results, implement cache, and
          realize the low level code generation. The store from the
          ``firepit`` package provides an operation abstraction
          over the raw internal database: either a local store, e.g., SQLite,
          or a remote one, e.g., PostgreSQL. If not specified from the
          constructor parameter, the session will use the default SQLite
          store in the :attr:`runtime_directory`.

        debug_mode (bool): The debug flag set by the session constructor. If
          True, a fixed debug link ``/tmp/kestrel`` of :attr:`runtime_directory`
          will be created, and :attr:`runtime_directory` will not be removed by
          the session when terminating.

        runtime_directory_is_owned_by_upper_layer (bool): The flag to specify
          who owns and manages :attr:`runtime_directory`. False by default,
          where the Kestrel session will manage session file system isolation --
          create and destory :attr:`runtime_directory`. If True, the runtime
          directory is created, passed in to the session constructor, and will
          be destroyed by the calling site.

        symtable (dict): The continuously updated *symbol table* of the running
          session, which is a dictionary mapping from Kestrel variable names
          ``str`` to their associated Kestrel internal data structure
          ``VarStruct``.

        data_source_manager (kestrel.datasource.DataSourceManager): The
          data source manager handles queries to all data source interfaces such as
          local file stix bundle and stix-shifter. It also stores previous
          queried data sources for the session, which is used for a syntax
          sugar when there is no data source in a Kestrel ``GET`` statement -- the
          last data source is implicitly used.

        analytics_manager (kestrel.analytics.AnalyticsManager): The analytics
          manager handles all analytics related operations such as executing an
          analytics or getting the list of analytics for code auto-completion.

    """

    def __init__(
        self, session_id=None, runtime_dir=None, store_path=None, debug_mode=False
    ):
        _logger.debug(
            f"Establish session with session_id: {session_id}, runtime_dir: {runtime_dir}, store_path:{store_path}, debug_mode:{debug_mode}"
        )

        self.config = self._load_configuration()

        if session_id:
            self.session_id = session_id
        else:
            self.session_id = str(uuid.uuid4())

        self.debug_mode = (
            True
            if debug_mode
            or os.getenv(self.config["session"]["debug_env_var_name"], False)
            else False
        )

        # default value of runtime_directory ownership
        self.runtime_directory_is_owned_by_upper_layer = False

        # runtime (temporary) directory to store session-related data
        sys_tmp_dir = pathlib.Path(tempfile.gettempdir())
        if runtime_dir:
            if os.path.exists(runtime_dir):
                self.runtime_directory_is_owned_by_upper_layer = True
            else:
                pathlib.Path(runtime_dir).mkdir(parents=True, exist_ok=True)
            self.runtime_directory = runtime_dir
        else:
            tmp_dir = sys_tmp_dir / ("kestrel-session-" + self.session_id)
            self.runtime_directory = tmp_dir.resolve()
            if tmp_dir.exists():
                if tmp_dir.is_dir():
                    _logger.debug(
                        "Kestrel session with runtime_directory exists, reuse it."
                    )
                else:
                    _logger.debug(
                        "strange tmp file that uses kestrel session dir name, remove it."
                    )
                    os.remove(self.runtime_directory)
            else:
                _logger.debug(
                    f"create new session runtime_directory: {self.runtime_directory}."
                )
                tmp_dir.mkdir(parents=True, exist_ok=True)

        if self.debug_mode:
            runtime_directory_master = sys_tmp_dir / "kestrel"
            if runtime_directory_master.exists():
                runtime_directory_master.unlink()
            runtime_directory_master.symlink_to(self.runtime_directory)

        # local database of SQLite or Parquet
        if not store_path:
            # use the default local database in config.py
            store_path = os.path.join(
                self.runtime_directory, self.config["session"]["local_database_path"]
            )
        self.store = get_storage(store_path, self.session_id)

        # Symbol Table
        # linking variables in syntax with internal data structure
        # handling fallback_var for the most recently accessed var
        # {"var": VarStruct}
        self.symtable = {}

        self.data_source_manager = DataSourceManager()
        self.analytics_manager = AnalyticsManager()
        iso_ts_regex = r"\d{4}(-\d{2}(-\d{2}(T\d{2}(:\d{2}(:\d{2}Z?)?)?)?)?)?"
        self._iso_ts = re.compile(iso_ts_regex)

    def execute(self, codeblock):
        """Execute a Kestrel code block.

        A Kestrel statement or multiple consecutive statements constitute a code
        block, which can be executed by this method. New Kestrel variables can be
        created in a code block such as ``newvar = GET ...``. Two types of Kestrel
        variables can be legally referred in a Kestrel statement in the code block:

        * A Kestrel variable created in the same code block prior to the reference.

        * A Kestrel variable created in code blocks previously executed by the
          session. The session maintains the :attr:`symtable` to keep the state
          of all previously executed Kestrel statements and their established Kestrel
          variables.

        Args:
            codeblock (str): the code block to be executed.

        Returns:
            A list of outputs that each of them is the output for each
            statement in the inputted code block.
        """
        ast = self.parse(codeblock)
        return self._execute_ast(ast)

    def parse(self, codeblock):
        """Parse a Kestrel code block.

        Parse one or multiple consecutive Kestrel statements (a Kestrel code block)
        into the abstract syntax tree. This could be useful for frontends that
        need to parse a statement *without* executing it in order to render
        some type of interface.

        Args:
            codeblock (str): the code block to be parsed.

        Returns:
            A list of dictionaries that each of them is an *abstract syntax
            tree* for one Kestrel statement in the inputted code block.
        """
        try:
            ast = parse(
                codeblock,
                self.config["language"]["default_variable"],
                self.config["language"]["default_sort_order"],
            )
        except UnexpectedCharacters as err:
            raise KestrelSyntaxError(err.line, err.column, "character", err.char)
        except UnexpectedToken as err:
            raise KestrelSyntaxError(err.line, err.column, "token", err.token)
        return ast

    def get_variable_names(self):
        """Get the list of Kestrel variable names created in this session."""
        return list(self.symtable.keys())

    def get_variable(self, var_name):
        """Get the data of Kestrel variable ``var_name``, which is list of homogeneous entities (STIX SCOs)."""
        # In the future, consider returning a generator here?
        return self.symtable[var_name].get_entities()

    def create_variable(self, var_name, objects, object_type=None):
        """Create a new Kestrel variable ``var_name`` with data in ``objects``.

        This is the API equivalent to Kestrel command ``NEW``, while allowing more
        flexible objects types (Python objects) than the objects serialized
        into text/JSON in the command ``NEW``.

        Args:

            var_name (str): The Kestrel variable to be created.

            objects (list): List of Python objects, currently support either a
              list of ``str`` or a list of ``dict``.

            object_type (str): The Kestrel entity type for the created Kestrel
              variable. It overrides the ``type`` field in ``objects``. If
              there is no ``type`` field in ``objects``, e.g., ``objects`` is a
              list of ``str``, this parameter is required.

        """
        virtual_stmt_ast = [
            {"command": "new", "output": var_name, "data": objects, "type": object_type}
        ]
        self._execute_ast(virtual_stmt_ast)

    def do_complete(self, code, cursor_pos):
        """Kestrel code auto-completion.

        This function gives a list of suggestions on the inputted partial Kestrel
        code to complete it. The current version sets the context for
        completion on word level -- it will reason around the last word in the
        input Kestrel code to provide suggestions. Data sources and analytics names
        can also be completed since the entire URI are single words (no space
        in data source or analytic name string). This feature can be used to
        list all available data sources or analytics, e.g., giving the last
        partial word ``stixshifter://``.

        Currently this method computes code completion based on:

        * Kestrel keywords
        * Kestrel variables
        * data source names
        * analytics names

        Args:
            code (str): Kestrel code.
            cursor_pos (int): the position to start completion (index in ``code``).

        Returns:
            A list of suggested strings to complete the code.
        """
        prefix = code[:cursor_pos]
        last_word = prefix.split(" ")[-1]

        if "START" in prefix or "STOP" in prefix:
            return self._get_complete_timestamp(last_word)
        elif "://" in last_word:
            scheme, path = last_word.split("://")
            if scheme in self.data_source_manager.schemes():
                data_source_names = (
                    self.data_source_manager.list_data_sources_from_scheme(scheme)
                )
                allnames = [scheme + "://" + name for name in data_source_names]
                _logger.debug(
                    f"auto-complete from data source interface {scheme}: {allnames}"
                )
            elif scheme in self.analytics_manager.schemes():
                analytics_names = self.analytics_manager.list_analytics_from_scheme(
                    scheme
                )
                allnames = [scheme + "://" + name for name in analytics_names]
                _logger.debug(
                    f"auto-complete from analytics interface {scheme}: {allnames}"
                )
            else:
                allnames = []
                _logger.debug("cannot find auto-complete interface")
        else:
            allnames = (
                get_keywords()
                + self.get_variable_names()
                + self.data_source_manager.schemes()
                + self.analytics_manager.schemes()
            )
            _logger.debug("standard auto-complete")

        suggestions = [
            name[len(last_word) :] for name in allnames if name.startswith(last_word)
        ]
        return suggestions

    def close(self):
        """Explicitly close the session.

        Only needed for non-context-managed sessions.
        """
        del self.store
        if not self.runtime_directory_is_owned_by_upper_layer and not self.debug_mode:
            shutil.rmtree(self.runtime_directory)

    def _execute_ast(self, ast):
        displays = []
        new_vars = []

        start_exec_ts = time.time()
        for stmt in ast:

            try:

                # pre-processing: semantics check and completion
                #   - ensure all parsed elements not empty
                #   - check existance of argument variables
                #   - complete data source if omitted by user
                #   - complete input context
                check_elements_not_empty(stmt)
                for input_var_name in get_all_input_var_names(stmt):
                    check_var_exists(input_var_name, self.symtable)
                if stmt["command"] == "get":
                    recognize_var_source(stmt, self.symtable)
                    complete_data_source(
                        stmt, self.data_source_manager.queried_data_sources[-1]
                    )
                if stmt["command"] == "load" or stmt["command"] == "save":
                    stmt["path"] = pathlib.Path(stmt["path"]).resolve()
                if stmt["command"] == "find":
                    check_semantics_on_find(stmt, self.symtable[stmt["input"]].type)
                if "attrs" in stmt:
                    var_struct = self.symtable[stmt["input"]]
                    stmt["attrs"] = normalize_attrs(stmt, var_struct)

                # code generation and execution
                execute_cmd = getattr(commands, stmt["command"])

                # set current working directory for each command execution
                # use this to implicitly pass runtime_dir as an argument to each command
                # the context manager switch back cwd when the command execution completes
                with set_current_working_directory(self.runtime_directory):
                    output_var_struct, display = execute_cmd(stmt, self)

            # exception completion
            except StixPatternError as e:
                raise InvalidStixPattern(e.stix)

            # post-processing: symbol table update
            if output_var_struct is not None:
                output_var_name = stmt["output"]
                self._update_symbol_table(output_var_name, output_var_struct)

                if output_var_name != self.config["language"]["default_variable"]:
                    if output_var_name in new_vars:
                        new_vars.remove(output_var_name)
                    new_vars.append(output_var_name)

            if display is not None:
                displays.append(display)

        end_exec_ts = time.time()
        execution_time_sec = math.ceil(end_exec_ts - start_exec_ts)

        if new_vars:
            vars_summary = [
                gen_variable_summary(vname, self.symtable[vname]) for vname in new_vars
            ]
            displays.append(DisplayBlockSummary(vars_summary, execution_time_sec))

        return displays

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _update_symbol_table(self, output_var_name, output_var_struct):
        self.symtable[output_var_name] = output_var_struct
        self.symtable[self.config["language"]["default_variable"]] = output_var_struct

    def _load_configuration(self):

        configs = []

        for path in config_paths():
            try:
                configs.append(toml.load(path))
                _logger.debug(f"Configuration file {path} loaded successfully.")
            except FileNotFoundError:
                _logger.debug(f"Configuration file {path} does not exist.")
            except toml.decoder.TomlDecodeError:
                _logger.debug(f"Invalid configuration file {path}.")

        if not configs:
            raise NoValidConfiguration
        else:
            config = configs.pop(0)
            for c in configs:
                config.update(c)

        _logger.debug(f"Configuration loaded: {config}")

        return config

    def _get_complete_timestamp(self, ts_str):
        valid_ts_formats = [
            "%Y",
            "%Y-%m",
            "%Y-%m-%d",
            "%Y-%m-%dT%H",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
        ]
        complete_ts = []
        for vts in valid_ts_formats:
            ts = ts_str.split("'")[-1]
            matched = self._iso_ts.match(ts)
            if matched:
                try:
                    ts_iso = datetime.strptime(matched.group(), vts).isoformat()
                    complete_ts.append(ts_iso[len(ts) :] + "Z'")
                    if complete_ts:
                        return complete_ts
                except:
                    _logger.debug(f"Try to match timestamp {ts} by format {vts}")
                    pass
