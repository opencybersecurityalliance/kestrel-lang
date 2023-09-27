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
import getpass
import pathlib
import shutil
import uuid
import logging
import time
import math
import lark
import atexit
from contextlib import AbstractContextManager

from kestrel.exceptions import (
    KestrelSyntaxError,
    InvalidStixPattern,
    DebugCacheLinkOccupied,
)
from kestrel.syntax.parser import parse_kestrel
from kestrel.semantics.processor import semantics_processing
from kestrel.semantics.completor import do_complete
from kestrel.codegen import commands
from kestrel.codegen.display import DisplayBlockSummary
from kestrel.codegen.summary import gen_variable_summary
from kestrel.symboltable.symtable import SymbolTable
from kestrel.utils import (
    set_current_working_directory,
    resolve_path_in_kestrel_env_var,
    add_logging_handler,
)
from kestrel.config import load_config
from kestrel.datasource import DataSourceManager
from kestrel.analytics import AnalyticsManager
from firepit import get_storage
from firepit.exceptions import StixPatternError

_logger = logging.getLogger(__name__)


class Session(AbstractContextManager):
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

        resolve_path_in_kestrel_env_var()

        self.config = load_config()

        if session_id:
            self.session_id = session_id
        else:
            self.session_id = str(uuid.uuid4())

        self.debug_mode = (
            True
            if debug_mode or os.getenv(self.config["debug"]["env_var"], False)
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
            tmp_dir = sys_tmp_dir / (
                self.config["session"]["cache_directory_prefix"]
                + str(os.getuid())
                + "-"
                + self.session_id
            )
            self.runtime_directory = tmp_dir.expanduser().resolve()
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
            self._setup_runtime_directory_master()

        self._logging_setup()

        # local database of SQLite or PostgreSQL
        if not store_path:
            # use the default local database in config.py
            local_database_path = self.config["session"]["local_database_path"]
            if "://" in local_database_path:
                store_path = local_database_path
            else:
                store_path = os.path.join(self.runtime_directory, local_database_path)
        self.store = get_storage(store_path, self.session_id)

        # Symbol Table
        # linking variables in syntax with internal data structure
        # handling fallback_var for the most recently accessed var
        # {"var": VarStruct}
        self.symtable = SymbolTable()

        self.data_source_manager = DataSourceManager(self.config)
        self.analytics_manager = AnalyticsManager(self.config)

        atexit.register(self.close)

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
            ast = parse_kestrel(
                codeblock,
                self.config["language"]["default_variable"],
                self.config["language"]["default_sort_order"],
            )
        except lark.UnexpectedEOF as err:
            # use `err.expected` as used in lark.exceptions.UnexpectedEOF
            raise KestrelSyntaxError(
                err.line, err.column, "end of line", "", err.expected
            )
        except lark.UnexpectedCharacters as err:
            # use `err.allowed` as used in lark.exceptions.UnexpectedCharacters
            raise KestrelSyntaxError(
                err.line, err.column, "character", err.char, err.allowed
            )
        except lark.UnexpectedToken as err:
            # use `err.accepts or err.expected` as used in lark.exceptions.UnexpectedToken
            raise KestrelSyntaxError(
                err.line, err.column, "token", err.token, err.accepts or err.expected
            )
        return ast

    def get_variable_names(self):
        """Get the list of Kestrel variable names created in this session."""
        return list(self.symtable.keys())

    def get_variable(self, var_name, deref=True):
        """Get the data of Kestrel variable ``var_name``, which is list of homogeneous entities (STIX SCOs)."""
        # In the future, consider returning a generator here?
        return self.symtable[var_name].get_entities(deref)

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

        Args:
            code (str): Kestrel code.
            cursor_pos (int): the position to start completion (index in ``code``).

        Returns:
            A list of suggested strings to complete the code.
        """
        return do_complete(
            code,
            cursor_pos,
            self.data_source_manager,
            self.analytics_manager,
            self.symtable,
        )

    def close(self):
        """Explicitly close the session.

        This may be executed by a context manager or when the program exits.
        """
        # Note there are two conditions that trigger this function, so it is probably executed twice
        # Be careful to write the logic in this function to avoid deleting nonexist files/dirs

        # remove logging handler
        if self.logging_handler:
            logging.getLogger().removeHandler(self.logging_handler)
            self.logging_handler.close()
            # ensure this does not executed twice
            self.logging_handler = None

        if self.original_logging_level:
            logging.getLogger().setLevel(self.original_logging_level)

        # close store/database
        if self.store:
            # release resources
            self.store.close()
            # ensure this does not executed twice
            self.store = None

        # manage temp folder for debug
        # ensure this does not execute if already executed
        if os.path.exists(self.runtime_directory):
            if not self.runtime_directory_is_owned_by_upper_layer:
                if self.debug_mode:
                    self._leave_exit_marker()
                    self._remove_obsolete_debug_folders()
                else:
                    shutil.rmtree(self.runtime_directory)

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _execute_ast(self, ast):
        displays = []
        new_vars = []

        start_exec_ts = time.time()
        for stmt in ast:
            try:
                # semantic checking and unfolding
                semantics_processing(
                    stmt,
                    self.symtable,
                    self.store,
                    self.data_source_manager,
                    self.config,
                )

                # code generation and execution
                execute_cmd = getattr(commands, stmt["command"])

                # set current working directory for each command execution
                # use this to implicitly pass runtime_dir as an argument to each command
                # the context manager switch back cwd when the command execution completes
                with set_current_working_directory(self.runtime_directory):
                    output_var_struct, display = execute_cmd(stmt, self)

            # exception completion
            except StixPatternError as e:
                raise InvalidStixPattern(e.stix) from e

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

        if self.config["session"]["show_execution_summary"] and new_vars:
            vars_summary = [
                gen_variable_summary(vname, self.symtable[vname]) for vname in new_vars
            ]
            displays.append(DisplayBlockSummary(vars_summary, execution_time_sec))

        return displays

    def _update_symbol_table(self, output_var_name, output_var_struct):
        self.symtable[output_var_name] = output_var_struct
        self.symtable[self.config["language"]["default_variable"]] = output_var_struct

    def _leave_exit_marker(self):
        runtime_dir = pathlib.Path(self.runtime_directory)
        exit_marker = runtime_dir / self.config["debug"]["session_exit_marker"]
        exit_marker.touch()

    def _remove_obsolete_debug_folders(self):
        # will only clean debug cache directories under system temp directory

        # [(cache_dir, timestamp)]
        exited_sessions = []

        for x in pathlib.Path(tempfile.gettempdir()).iterdir():
            if x.is_dir() and x.parts[-1].startswith(
                self.config["session"]["cache_directory_prefix"]
                + str(os.getuid())
                + "-"
            ):
                marker = x / self.config["debug"]["session_exit_marker"]
                if marker.exists():
                    exited_sessions.append((x, marker.stat().st_mtime))

        # preserve the newest self.config["debug"]["maximum_exited_session"] debug sessions
        exited_sessions.sort(key=lambda x: x[1])
        for x, _ in exited_sessions[: -self.config["debug"]["maximum_exited_session"]]:
            shutil.rmtree(x)

    def _get_runtime_directory_master(self):
        sys_tmp_dir = pathlib.Path(tempfile.gettempdir())

        user_suffix = None
        for f in [getpass.getuser, os.getuid]:
            if not user_suffix:
                try:
                    user_suffix = f()
                except:
                    pass
        if not user_suffix:
            user_suffix = "noUID"

        return sys_tmp_dir / (
            self.config["debug"]["cache_directory_prefix"] + user_suffix
        )

    def _setup_runtime_directory_master(self):
        master_dir = self._get_runtime_directory_master()

        # master_dir.exists() should not be used
        # it will return False for broken link
        try:
            master_dir.unlink()
        except FileNotFoundError:
            pass
        except PermissionError:
            raise DebugCacheLinkOccupied(master_dir.resolve())

        master_dir.symlink_to(self.runtime_directory)

    def _logging_setup(self):
        log_file_name = self.config["session"]["log_path"]
        log_file_path = os.path.join(self.runtime_directory, log_file_name)
        handler = logging.FileHandler(log_file_path)
        self.logging_handler, self.original_logging_level = add_logging_handler(
            handler, self.debug_mode
        )
