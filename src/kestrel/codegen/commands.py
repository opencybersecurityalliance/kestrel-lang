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
from copy import deepcopy

from firepit.deref import auto_deref
from firepit.exceptions import InvalidAttr
from firepit.query import Limit, Offset, Order, Predicate, Projection, Query
from firepit.stix20 import summarize_pattern

from kestrel.semantics.reference import make_deref_func, make_var_timerange_func
from kestrel.utils import remove_empty_dicts, dedup_ordered_dicts, lowered_str_list
from kestrel.exceptions import *
from kestrel.symboltable.variable import new_var
from kestrel.symboltable.symtable import SymbolTable
from kestrel.syntax.parser import parse_ecgpattern
from kestrel.syntax.utils import (
    get_entity_types,
    get_all_input_var_names,
    timedelta_seconds,
)
from kestrel.codegen.data import load_data, load_data_file, dump_data_to_file
from kestrel.codegen.display import DisplayDataframe, DisplayDict, DisplayWarning
from kestrel.codegen.queries import (
    compile_specific_relation_to_query,
    compile_generic_relation_to_query,
)
from kestrel.codegen.relations import (
    generic_relations,
    compile_identical_entity_search_pattern,
    fine_grained_relational_process_filtering,
    get_entity_id_attribute,
    stix_2_0_identical_mapping,
    build_pattern_from_ids,
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
        for varname in get_all_input_var_names(stmt):
            v = session.symtable[varname]
            if v.length + v.records_count == 0:
                raise EmptyInputVariable(varname)
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
def assign(stmt, session):
    entity_table = session.symtable[stmt["input"]].entity_table
    transform = stmt.get("transform")
    if transform:
        if transform.lower() == "timestamped":
            qry = session.store.timestamped(entity_table, run=False)
        else:
            qry = Query(entity_table)
    else:
        qry = Query(entity_table)

    qry = _build_query(session.store, entity_table, qry, stmt)

    try:
        session.store.assign_query(stmt["output"], qry)
        output = new_var(session.store, stmt["output"], [], stmt, session.symtable)
    except InvalidAttr as e:
        var_attr = str(e).split()[-1]
        var_name, _, attr = var_attr.rpartition(".")
        raise MissingEntityAttribute(var_name, attr) from e

    return output, None


@_debug_logger
@_default_output
def merge(stmt, session):
    entity_types = list(
        set([session.symtable[var_name].type for var_name in stmt["inputs"]])
    )
    if len(entity_types) > 1:
        raise NonUniformEntityType(entity_types)
    entity_tables = [
        session.symtable[var_name].entity_table for var_name in stmt["inputs"]
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
        session.store, session.symtable[stmt["input"]].entity_table, stmt["path"]
    )
    return None, None


@_debug_logger
def info(stmt, session):
    header = session.store.columns(session.symtable[stmt["input"]].entity_table)
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
    entity_table = session.symtable[stmt["input"]].entity_table
    transform = stmt.get("transform")
    if transform and entity_table:
        if transform.lower() == "timestamped":
            qry = session.store.timestamped(entity_table, run=False)
        else:
            qry = Query(entity_table)
    else:
        qry = Query(entity_table)

    qry = _build_query(session.store, entity_table, qry, stmt)
    try:
        cursor = session.store.run_query(qry)
    except InvalidAttr as e:
        var_attr = str(e).split()[-1]
        var_name, _, attr = var_attr.rpartition(".")
        raise MissingEntityAttribute(var_name, attr) from e
    content = cursor.fetchall()

    return None, DisplayDataframe(dedup_ordered_dicts(remove_empty_dicts(content)))


@_debug_logger
@_default_output
def get(stmt, session):
    pattern = stmt["stixpattern"]
    local_var_table = stmt["output"] + "_local"
    return_var_table = stmt["output"]
    return_type = stmt["type"]
    start_offset = session.config["stixquery"]["timerange_start_offset"]
    end_offset = session.config["stixquery"]["timerange_stop_offset"]
    display = None

    if "variablesource" in stmt:
        input_type = session.symtable[stmt["variablesource"]].type
        output_type = stmt["type"]
        if input_type != output_type:
            raise InvalidECGPattern(
                f"input variable type {input_type} does not match output type {output_type}"
            )
        session.store.filter(
            stmt["output"],
            stmt["type"],
            input_type,
            pattern,
        )
        output = new_var(session.store, return_var_table, [], stmt, session.symtable)
        _logger.debug(f"get from variable source \"{stmt['variablesource']}\"")

    elif "datasource" in stmt:
        # rs: RetStruct
        rs = session.data_source_manager.query(
            stmt["datasource"], pattern, session.session_id
        )
        query_id = rs.load_to_store(session.store)
        session.store.extract(local_var_table, return_type, query_id, pattern)
        _output = new_var(session.store, local_var_table, [], stmt, session.symtable)
        _logger.debug(
            f"native GET pattern executed and DB view {local_var_table} extracted."
        )

        pat_summary = summarize_pattern(pattern)
        pat_types = list(pat_summary.keys())
        if return_type in stix_2_0_identical_mapping:
            id_attrs = set(stix_2_0_identical_mapping[return_type])
        else:
            id_attrs = pat_summary[return_type]  # Hack
        if (
            len(pat_types) == 1
            and pat_types[0] == return_type
            and pat_summary[return_type] == id_attrs
        ):
            # Prefetch won't return anything new here, so skip it
            _logger.debug("To skip prefetch for direct query")
            is_direct_query = True
        else:
            is_direct_query = False

        if (
            not is_direct_query
            and _is_prefetch_allowed_in_config(
                session.config["prefetch"], "get", return_type
            )
            and len(_output)
        ):
            prefetch_ret_var_table = return_var_table + "_prefetch"
            ext_graph_pattern = deepcopy(stmt["where"])
            ext_graph_pattern.prune_away_centered_graph(return_type)
            prefetch_ret_entity_table = _prefetch(
                return_type,
                prefetch_ret_var_table,
                local_var_table,
                stmt["timerange"],
                start_offset,
                end_offset,
                SymbolTable({local_var_table: _output}),
                session.store,
                ext_graph_pattern,
                session.session_id,
                session.data_source_manager,
                session.config["stixquery"]["support_id"],
            )

            if return_type == "process" and get_entity_id_attribute(_output) != "id":
                prefetch_ret_entity_table = _filter_prefetched_process(
                    return_var_table,
                    session,
                    _output,
                    prefetch_ret_entity_table,
                    return_type,
                )
        else:
            prefetch_ret_entity_table = None

        if prefetch_ret_entity_table:
            _logger.debug(
                f"merge {local_var_table} and {prefetch_ret_entity_table} into {return_var_table}."
            )
            session.store.merge(
                return_var_table, [local_var_table, prefetch_ret_entity_table]
            )
            for v in list(
                set(
                    [local_var_table, prefetch_ret_entity_table, prefetch_ret_var_table]
                )
            ):
                if not session.debug_mode:
                    _logger.debug(f"remove temp store view {v}.")
                    session.store.remove_view(v)
        else:
            _logger.debug(
                f'prefetch return None, just rename native GET pattern matching results into "{return_var_table}".'
            )
            session.store.rename_view(local_var_table, return_var_table)

        output = new_var(session.store, return_var_table, [], stmt, session.symtable)

        if not len(output):
            if not return_type.startswith("x-") and return_type not in (
                set(session.store.types()) | set(get_entity_types())
            ):
                display = DisplayWarning(f'unknown entity type "{return_type}"')
    else:
        raise KestrelInternalError(f"unknown type of source in {str(stmt)}")

    return output, display


@_debug_logger
@_default_output
@_guard_empty_input
def find(stmt, session):
    return_type = stmt["type"]
    input_type = session.symtable[stmt["input"]].type
    input_var_name = stmt["input"]
    return_var_table = stmt["output"]
    local_var_table = stmt["output"] + "_local"
    relation = stmt["relation"]
    is_reversed = stmt["reversed"]
    start_offset = session.config["stixquery"]["timerange_start_offset"]
    end_offset = session.config["stixquery"]["timerange_stop_offset"]
    rel_query = None

    if return_type not in session.store.types():
        # return empty variable
        output = new_var(session.store, None, [], stmt, session.symtable)

    else:
        _symtable = SymbolTable({input_var_name: session.symtable[input_var_name]})
        input_var_attrs = session.store.columns(input_type)
        return_type_attrs = session.store.columns(return_type)

        # First, get information from local store
        if relation in generic_relations:
            rel_query = compile_generic_relation_to_query(
                return_type, input_type, session.symtable[input_var_name].entity_table
            )

        else:
            rel_query = compile_specific_relation_to_query(
                return_type,
                relation,
                input_type,
                is_reversed,
                input_var_name,
                input_var_attrs,
                return_type_attrs,
            )

        # `session.store.assign_query` will generate new entity_table named `local_var_table`
        if rel_query:
            session.store.assign_query(local_var_table, rel_query, return_type)
            _output = new_var(
                session.store, local_var_table, [], stmt, session.symtable
            )

            # Second, prefetch all records of the entities and associated entities
            if (
                _is_prefetch_allowed_in_config(
                    session.config["prefetch"], "find", return_type
                )
                and len(_output)
                and _output.data_source
            ):
                prefetch_ret_var_table = return_var_table + "_prefetch"
                ext_graph_pattern = stmt["where"] if "where" in stmt else None
                prefetch_ret_entity_table = _prefetch(
                    return_type,
                    prefetch_ret_var_table,
                    local_var_table,
                    stmt["timerange"],
                    start_offset,
                    end_offset,
                    SymbolTable({local_var_table: _output}),
                    session.store,
                    ext_graph_pattern,
                    session.session_id,
                    session.data_source_manager,
                    session.config["stixquery"]["support_id"],
                )

                # special handling for process to filter out impossible relational processes
                # this is needed since STIX 2.0 does not have mandatory fields for
                # process and field like `pid` is not unique
                if (
                    return_type == "process"
                    and get_entity_id_attribute(_output) != "id"
                ):
                    prefetch_ret_entity_table = _filter_prefetched_process(
                        return_var_table,
                        session,
                        _output,
                        prefetch_ret_entity_table,
                        return_type,
                    )
            else:
                prefetch_ret_entity_table = None

            if prefetch_ret_entity_table:
                _logger.debug(
                    f"merge {local_var_table} and {prefetch_ret_entity_table} into {return_var_table}."
                )
                session.store.merge(
                    return_var_table, [local_var_table, prefetch_ret_entity_table]
                )
                for v in list(
                    set(
                        [
                            local_var_table,
                            prefetch_ret_entity_table,
                            prefetch_ret_var_table,
                        ]
                    )
                ):
                    if not session.debug_mode:
                        _logger.debug(f"remove temp store view {v}.")
                        session.store.remove_view(v)
            else:
                _logger.debug(
                    f'prefetch return None, just rename native GET pattern matching results into "{return_var_table}".'
                )
                session.store.rename_view(local_var_table, return_var_table)

        else:
            return_var_table = None
            _logger.info(f'no relation "{relation}" on this dataset')

        output = new_var(session.store, return_var_table, [], stmt, session.symtable)

    return output, None


@_debug_logger
@_default_output
@_guard_empty_input
def join(stmt, session):
    session.store.join(
        stmt["output"],
        session.symtable[stmt["input"]].entity_table,
        stmt["attribute_1"],
        session.symtable[stmt["input_2"]].entity_table,
        stmt["attribute_2"],
    )


@_debug_logger
@_default_output
@_guard_empty_input
def group(stmt, session):
    if "aggregations" in stmt:
        aggs = [(i["func"], i["attr"], i["alias"]) for i in stmt["aggregations"]]
    else:
        aggs = None
    session.store.group(
        stmt["output"],
        session.symtable[stmt["input"]].entity_table,
        stmt["attributes"],
        aggs,
    )


@_debug_logger
@_default_output
@_guard_empty_input
def sort(stmt, session):
    session.store.assign(
        stmt["output"],
        session.symtable[stmt["input"]].entity_table,
        op="sort",
        by=stmt["attribute"],
        ascending=stmt["ascending"],
    )


@_debug_logger
@_default_output
@_guard_empty_input
def apply(stmt, session):
    arg_vars = [session.symtable[v_name] for v_name in stmt["inputs"]]
    display = session.analytics_manager.execute(
        stmt["analytics_uri"], arg_vars, session.session_id, stmt["arguments"]
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
    where_clause,
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

        time_range ((datetime, datetime)).

        start_offset (int): start time offset by seconds.

        end_offset (int): end time offset by seconds.

        symtable ({str:VarStruct}): should has ``input_var_name``.

        store (firepit.SqlStorage): store.

        where_clause (ExtCenteredGraphPattern): pattern to merge to the prefetch auto-gen pattern

        session_id (str): session ID.

        does_support_id (bool): whether "id" can be an attribute in data source query.

    Returns:
        str: the entity table in store if the prefetch is performed else None.
    """

    _logger.debug(f"prefetch {return_type} to extend {input_var_name}.")

    pattern_raw = compile_identical_entity_search_pattern(
        input_var_name, symtable[input_var_name], does_support_id
    )

    if pattern_raw:
        pattern_ast = parse_ecgpattern(pattern_raw)
        deref_func = make_deref_func(store, symtable)
        get_timerange_func = make_var_timerange_func(store, symtable)
        pattern_ast.deref(deref_func, get_timerange_func)
        pattern_ast.add_center_entity(symtable[input_var_name].type)
        time_adj = tuple(map(timedelta_seconds, (start_offset, end_offset)))
        _logger.info(f"ext pattern in prefetch: {where_clause}")
        _logger.info(f"prefetch pattern before extend: {pattern_ast}")
        pattern_ast.extend("AND", where_clause)
        _logger.info(f"prefetch pattern after extend: {pattern_ast}")
        stix_pattern = pattern_ast.to_stix(time_range, time_adj)
        _logger.info(f"STIX pattern generated in prefetch: {stix_pattern}")

        if stix_pattern:
            data_source = symtable[input_var_name].data_source
            resp = ds_manager.query(data_source, stix_pattern, session_id)
            query_id = resp.load_to_store(store)

            # build the return_var_name view in store
            store.extract(return_var_name, return_type, query_id, stix_pattern)

            _logger.debug(f"prefetch successful.")
            return return_var_name

    _logger.info(f"prefetch return empty.")
    return None


def _filter_prefetched_process(
    return_var_name, session, local_var, prefetched_entity_table, return_type
):
    _logger.debug(f"filter prefetched {return_type} for {prefetched_entity_table}.")

    prefetch_filtered_var_name = return_var_name + "_prefetch_filtered"
    entity_ids = fine_grained_relational_process_filtering(
        local_var,
        prefetched_entity_table,
        session.store,
        session.config["prefetch"]["process_identification"],
    )
    if entity_ids:
        id_pattern = build_pattern_from_ids(return_type, entity_ids)
        session.store.extract(prefetch_filtered_var_name, return_type, None, id_pattern)
        _logger.debug("filter successful.")
        return prefetch_filtered_var_name
    else:
        _logger.info("no prefetched process found after filtering.")
        return None


def _set_projection(store, entity_table, query, paths):
    joins, proj = auto_deref(store, entity_table, paths=paths)
    query.joins.extend(joins)
    joined = [j.name for j in query.joins]
    _logger.debug("%s: joining %s", query.table.name, joined)
    if query.proj:
        # Need to merge projections?  More-specific overrides less-specific ("*")
        new_cols = []
        for p in query.proj.cols:
            if not (hasattr(p, "table") and p.table == entity_table and p.name == "*"):
                new_cols.append(p)
        if proj:
            for p in proj.cols:
                if not (
                    hasattr(p, "table") and p.table == entity_table and p.name == "*"
                ):
                    new_cols.append(p)
        query.proj = Projection(new_cols)
    else:
        query.proj = proj


def _get_pred_columns(preds: list):
    for pred in preds:
        if isinstance(pred.lhs, Predicate):
            yield from _get_pred_columns([pred.lhs])
            if isinstance(pred.rhs, Predicate):
                yield from _get_pred_columns([pred.rhs])
        else:
            yield pred.lhs


def _get_filt_columns(filts: list):
    for filt in filts:
        yield from _get_pred_columns(filt.preds)


def _build_query(store, entity_table, qry, stmt):
    where = stmt.get("where")
    if where:
        if isinstance(where, Query):
            for j in where.joins:
                _logger.debug("Anchoring JOIN to %s", qry.table.name)
                j.prev_name = qry.table.name
            qry.joins.extend(where.joins)
            for col in _get_filt_columns(where.where):
                if col.table is None:
                    # Need to disambiguate any Predicate columns
                    _logger.debug("Disambiguating predicate for %s", qry.table.name)
                    col.table = qry.table.name
            qry.where.extend(where.where)
        else:
            where.set_table(entity_table)
            qry.append(where)
    attrs = stmt.get("attrs", "*")
    cols = attrs.split(",")
    _set_projection(store, entity_table, qry, cols)
    sort_by = stmt.get("attribute")
    if sort_by:
        direction = "ASC" if stmt["ascending"] else "DESC"
        qry.append(Order([(sort_by, direction)]))
    limit = stmt.get("limit")
    if limit:
        qry.append(Limit(limit))
    offset = stmt.get("offset")
    if offset:
        qry.append(Offset(offset))
    return qry


def _is_prefetch_allowed_in_config(pre_fetch_config, command_name, entity_type):
    if pre_fetch_config["switch_per_command"][
        command_name
    ] and entity_type not in lowered_str_list(pre_fetch_config["excluded_entities"]):
        return True
    else:
        return False
