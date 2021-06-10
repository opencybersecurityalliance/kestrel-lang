################################################################
#                       Module Summary
#
# - Code generation for each command in kestrel.lark
#   - The execution function names match commands in kestrel.lark
# - Each command takes 2 arguments
#     ( statement, session )
#   - statement is the current statement to process,
#     which is a dict from the parser
#   - session is the current session (context)
# - Every command returns a tuple (VarStruct, Display)
#   - VarStruct is a new object associated with the output var
#     - VarStruct associated with stmt["output"]
#     - None for some commands, e.g., DISP, SAVE, STAT
#   - Display is the data to display on the user interface
#     - a string
#     - a list of (str,str|list(str)) tuples
#     - a table that can be imported to pandas dataframe
################################################################

import functools
import logging
import itertools
from collections import OrderedDict

from kestrel.utils import remove_empty_dicts, dedup_ordered_dicts
from kestrel.exceptions import *
from kestrel.semantics import get_entity_table, get_entity_type, get_entity_len
from kestrel.symboltable import new_var
from kestrel.syntax.parser import get_all_input_var_names
from kestrel.codegen.data import load_data, load_data_file, dump_data_to_file
from kestrel.codegen.display import DisplayDataframe, DisplayDict
from kestrel.codegen.pattern import build_pattern, or_patterns
from kestrel.codegen.relations import (
    generic_relations,
    compile_generic_relation_to_pattern,
    compile_specific_relation_to_pattern,
    compile_identical_entity_search_pattern,
    compile_x_ibm_event_search_flow_in_pattern,
    compile_x_ibm_event_search_flow_out_pattern,
    are_entities_associated_with_x_ibm_event,
)

_logger = logging.getLogger(__name__)


################################################################
#                       Private Decorators
################################################################


def _default_output(func):
    # by default, create a table/view in the backend
    # using the output var name
    # in this case, the store backend can return no VarStruct
    @functools.wraps(func)
    def wrapper(stmt, session):
        ret = func(stmt, session)
        if not ret:
            var_struct = new_var(
                session.store, stmt["output"], [], stmt, session.symtable
            )
            return var_struct, None
        else:
            return ret

    return wrapper


def _guard_empty_input(func):
    @functools.wraps(func)
    def wrapper(stmt, session):
        input_len_dict = {
            v: get_entity_len(v, session.symtable)
            for v in get_all_input_var_names(stmt)
        }
        for v, size in input_len_dict.items():
            if size == 0:
                raise EmptyInputVariable(v)
        else:
            return func(stmt, session)

    return wrapper


def _debug_logger(func):
    @functools.wraps(func)
    def wrapper(stmt, session):
        _logger.debug(f"Executing '{func.__name__}' with statement: {stmt}")
        return func(stmt, session)

    return wrapper


################################################################
#                 Code Generation for Commands
################################################################


@_debug_logger
@_default_output
def merge(stmt, session):
    entity_types = list(
        set(
            [get_entity_type(var_name, session.symtable) for var_name in stmt["inputs"]]
        )
    )
    if len(entity_types) > 1:
        raise NonUniformEntityType(entity_types)
    entity_tables = [
        get_entity_table(var_name, session.symtable) for var_name in stmt["inputs"]
    ]
    session.store.merge(stmt["output"], entity_tables)
    output = new_var(session.store, stmt["output"], [], stmt, session.symtable)
    return output, None


@_debug_logger
@_default_output
def new(stmt, session):
    stmt["type"] = load_data(session.store, stmt["output"], stmt["data"], stmt["type"])


@_debug_logger
@_default_output
def load(stmt, session):
    stmt["type"] = load_data_file(
        session.store, stmt["output"], stmt["path"], stmt["type"]
    )


@_debug_logger
@_guard_empty_input
def save(stmt, session):
    dump_data_to_file(
        session.store, get_entity_table(stmt["input"], session.symtable), stmt["path"]
    )
    return None, None


@_debug_logger
def info(stmt, session):
    header = session.store.columns(get_entity_table(stmt["input"], session.symtable))
    direct_attrs, associ_attrs, custom_attrs, references = [], [], [], []
    for field in header:
        if field.startswith("x_"):
            custom_attrs.append(field)
        elif (
            field.endswith("_ref")
            or field.endswith("_refs")
            or field.endswith("_reference")
            or field.endswith("_references")
        ):
            # not useful in existing version, so do not display
            references.append(field)
        elif "_ref." in field or "_ref_" in field:
            associ_attrs.append(field)
        else:
            direct_attrs.append(field)

    disp = OrderedDict()
    disp["Entity Type"] = session.symtable[stmt["input"]].type
    disp["Number of Entities"] = str(len(session.symtable[stmt["input"]]))
    disp["Number of Records"] = str(session.symtable[stmt["input"]].records_count)
    disp["Entity Attributes"] = ", ".join(direct_attrs)
    disp["Indirect Attributes"] = [
        ", ".join(g)
        for _, g in itertools.groupby(associ_attrs, lambda x: x.rsplit(".", 1)[0])
    ]
    disp["Customized Attributes"] = ", ".join(custom_attrs)
    disp["Birth Command"] = session.symtable[stmt["input"]].birth_statement["command"]
    disp["Associated Datasource"] = session.symtable[stmt["input"]].data_source
    disp["Dependent Variables"] = ", ".join(
        session.symtable[stmt["input"]].dependent_variables
    )

    return None, DisplayDict(disp)


@_debug_logger
def disp(stmt, session):
    if len(session.symtable[stmt["input"]]) > 0:
        content = session.store.lookup(
            get_entity_table(stmt["input"], session.symtable),
            stmt["attrs"],
            stmt["limit"],
        )
    else:
        content = []
    return None, DisplayDataframe(dedup_ordered_dicts(remove_empty_dicts(content)))


@_debug_logger
@_default_output
def get(stmt, session):
    local_var_name = stmt["output"] + "_local"
    return_var_name = stmt["output"]
    return_type = stmt["type"]
    start_offset = session.config["stixquery"]["timerange_start_offset"]
    end_offset = session.config["stixquery"]["timerange_stop_offset"]

    pattern = build_pattern(
        stmt["patternbody"],
        stmt["timerange"],
        start_offset,
        end_offset,
        session.symtable,
        session.store,
    )

    if "variablesource" in stmt:
        session.store.filter(
            stmt["output"],
            stmt["type"],
            get_entity_table(stmt["variablesource"], session.symtable),
            pattern,
        )
        output = new_var(session.store, return_var_name, [], stmt, session.symtable)
        _logger.debug(f"get from variable source \"{stmt['variablesource']}\"")

    elif "datasource" in stmt:
        # rs: RetStruct
        rs = session.data_source_manager.query(
            stmt["datasource"], pattern, session.session_id
        )
        query_id = rs.load_to_store(session.store)
        session.store.extract(local_var_name, return_type, query_id, pattern)
        _output = new_var(session.store, local_var_name, [], stmt, session.symtable)

        output = _output

        if session.config["prefetch"]["get"] and len(_output):
            prefetch_ret_var_name = return_var_name + "_prefetch"
            prefetch_ret_entity_table = _prefetch(
                return_type,
                prefetch_ret_var_name,
                local_var_name,
                stmt["timerange"],
                start_offset,
                end_offset,
                {local_var_name: _output},
                session.store,
                session.session_id,
                session.data_source_manager,
                session.config["stixquery"]["support_id"],
            )
        else:
            prefetch_ret_entity_table = None

        if prefetch_ret_entity_table:
            session.store.merge(
                return_var_name, [local_var_name, prefetch_ret_entity_table]
            )
            output = new_var(session.store, return_var_name, [], stmt, session.symtable)
        else:
            output = new_var(session.store, local_var_name, [], stmt, session.symtable)

    else:
        raise KestrelInternalError(f"unknown type of source in {str(stmt)}")

    return output, None


@_debug_logger
@_default_output
@_guard_empty_input
def find(stmt, session):
    return_type = stmt["type"]
    input_type = session.symtable[stmt["input"]].type
    input_var_name = stmt["input"]
    return_var_name = stmt["output"]
    local_var_name = stmt["output"] + "_local"
    local_var_event_name = stmt["output"] + "_asso_event"
    relation = stmt["relation"]
    is_reversed = stmt["reversed"]
    time_range = stmt["timerange"]
    event_type = "x-oca-event"
    start_offset = session.config["stixquery"]["timerange_start_offset"]
    end_offset = session.config["stixquery"]["timerange_stop_offset"]

    if return_type not in session.store.tables():
        # return empty variable
        output = new_var(session.store, None, [], stmt, session.symtable)

    else:
        _symtable = {input_var_name: session.symtable[input_var_name]}

        event_pattern = None

        # First, get information from local store
        if relation in generic_relations:
            raw_pattern_body = compile_generic_relation_to_pattern(
                return_type, input_type, input_var_name
            )

            if (
                event_type in session.store.tables()
                and are_entities_associated_with_x_ibm_event([input_type, return_type])
                and input_type != return_type
            ):
                try:
                    event_in_pattern_body = compile_x_ibm_event_search_flow_in_pattern(
                        input_type, input_var_name
                    )
                    event_in_pattern = build_pattern(
                        event_in_pattern_body,
                        time_range,
                        start_offset,
                        end_offset,
                        _symtable,
                        session.store,
                    )
                    session.store.extract(
                        local_var_event_name, event_type, None, event_in_pattern
                    )
                    _symtable[local_var_event_name] = new_var(
                        session.store, local_var_event_name, [], stmt, session.symtable
                    )

                    event_out_pattern_body = (
                        compile_x_ibm_event_search_flow_out_pattern(
                            return_type, local_var_event_name
                        )
                    )
                    event_pattern = build_pattern(
                        event_out_pattern_body,
                        time_range,
                        start_offset,
                        end_offset,
                        _symtable,
                        session.store,
                    )
                except InvalidAttribute:
                    _logger.warning(
                        "attributes not in DB when building event pattern for x-oca-event"
                    )
        else:
            raw_pattern_body = compile_specific_relation_to_pattern(
                return_type, relation, input_type, is_reversed, input_var_name
            )

        try:
            local_pattern = build_pattern(
                raw_pattern_body,
                time_range,
                start_offset,
                end_offset,
                _symtable,
                session.store,
            )
        except InvalidAttribute:
            local_pattern = None

        local_pattern = or_patterns([local_pattern, event_pattern])
        if not local_pattern:
            _logger.info(f'no relation "{relation}" on this dataset')

        # by default, `session.store.extract` will generate new entity_table named `local_var_name`
        session.store.extract(local_var_name, return_type, None, local_pattern)

        _output = new_var(session.store, local_var_name, [], stmt, session.symtable)

        # default output without remote query
        output = _output

        # Second, prefetch all records of the entities and associated entities
        if session.config["prefetch"]["find"] and len(_output) and _output.data_source:
            prefetch_ret_var_name = return_var_name + "_prefetch"
            prefetch_ret_entity_table = _prefetch(
                return_type,
                prefetch_ret_var_name,
                local_var_name,
                time_range,
                start_offset,
                end_offset,
                {local_var_name: _output},
                session.store,
                session.session_id,
                session.data_source_manager,
                session.config["stixquery"]["support_id"],
            )
        else:
            prefetch_ret_entity_table = None

        if prefetch_ret_entity_table:
            session.store.merge(
                return_var_name, [local_var_name, prefetch_ret_entity_table]
            )
            output = new_var(session.store, return_var_name, [], stmt, session.symtable)
        else:
            output = new_var(session.store, local_var_name, [], stmt, session.symtable)

    return output, None


@_debug_logger
@_default_output
@_guard_empty_input
def join(stmt, session):
    session.store.join(
        stmt["output"],
        get_entity_table(stmt["input"], session.symtable),
        stmt["path"],
        get_entity_table(stmt["input_2"], session.symtable),
        stmt["path_2"],
    )


@_debug_logger
@_default_output
@_guard_empty_input
def group(stmt, session):
    session.store.assign(
        stmt["output"],
        get_entity_table(stmt["input"], session.symtable),
        op="group",
        by=stmt["path"],
    )


@_debug_logger
@_default_output
@_guard_empty_input
def sort(stmt, session):
    session.store.assign(
        stmt["output"],
        get_entity_table(stmt["input"], session.symtable),
        op="sort",
        by=stmt["path"],
        ascending=stmt["ascending"],
    )


@_debug_logger
@_default_output
@_guard_empty_input
def apply(stmt, session):
    arg_vars = [session.symtable[v_name] for v_name in stmt["inputs"]]
    display = session.analytics_manager.execute(
        stmt["workflow"], arg_vars, session.session_id, stmt["parameter"]
    )
    return None, display


################################################################
#                       Helper Functions
################################################################


def _prefetch(
    return_type,
    return_var_name,
    input_var_name,
    time_range,
    start_offset,
    end_offset,
    symtable,
    store,
    session_id,
    ds_manager,
    does_support_id,
):
    """prefetch identical entities and associated entities.

    Put the input entities in the center of an observation and query the remote
    data source of associated with input variable, so we get back:

    1. all records about the input entities.

    2. associated entities such as parent/child processes of processes, processes of network-traffic, etc.

    The function does not have explicit return, but a side effect: a view in
    the store named after `return_var_name`.

    Args:
        input_var_name (str): input variable name.

        return_var_name (str): return variable name.

        return_type (str): return entity type.

        time_range ((str, str)): start and end time in ISOTIMESTAMP.

        start_offset (int): start time offset by seconds.

        end_offset (int): end time offset by seconds.

        symtable ({str:VarStruct}): should has ``input_var_name``.

        store (firepit.SqlStorage): store.

        session_id (str): session ID.

        does_support_id (bool): whether "id" can be an attribute in data source query.

    Returns:
        str: the entity table in store if the prefetch is performed else None.
    """

    pattern_body = compile_identical_entity_search_pattern(
        input_var_name, symtable[input_var_name], does_support_id
    )

    if pattern_body:
        remote_pattern = build_pattern(
            pattern_body, time_range, start_offset, end_offset, symtable, store
        )

        if remote_pattern:
            data_source = symtable[input_var_name].data_source
            resp = ds_manager.query(data_source, remote_pattern, session_id)
            query_id = resp.load_to_store(store)

            # build the return_var_name view in store
            store.extract(return_var_name, return_type, query_id, remote_pattern)

            return return_var_name

    return None
