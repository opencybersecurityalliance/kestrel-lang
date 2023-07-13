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

from firepit.deref import auto_deref
from firepit.exceptions import InvalidAttr
from firepit.query import Limit, Offset, Order, Predicate, Projection, Query
from firepit.stix20 import summarize_pattern

from kestrel.utils import remove_empty_dicts, dedup_ordered_dicts
from kestrel.exceptions import *
from kestrel.symboltable.variable import new_var
from kestrel.syntax.utils import (
    get_entity_types,
    get_all_input_var_names,
)
from kestrel.codegen.data import load_data, load_data_file, dump_data_to_file
from kestrel.codegen.display import DisplayDataframe, DisplayDict, DisplayWarning
from kestrel.codegen.relations import (
    generic_relations,
    get_entity_id_attribute,
)
from kestrel.codegen.prefetch import do_prefetch
from kestrel.codegen.queries import (
    compile_specific_relation_to_query,
    compile_generic_relation_to_query,
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
    transform = stmt.get("transformer")
    if transform:
        qry = _transform_query(session.store, entity_table, transform)
    else:
        qry = Query(entity_table)

    qry = _build_query(session.store, entity_table, qry, stmt, [])

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
    transform = stmt.get("transformer")
    if transform and entity_table:
        qry = _transform_query(session.store, entity_table, transform)
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
    limit = stmt.get("limit")
    display = None

    if "variablesource" in stmt:
        input_type = session.symtable[stmt["variablesource"]].type
        output_type = stmt["type"]
        if input_type != output_type:
            raise InvalidECGPattern(
                f"input variable type {input_type} does not match output type {output_type}"
            )
        session.store.filter(
            return_var_table,
            return_type,
            input_type,
            pattern,
        )
        _logger.debug(f"get from variable source \"{stmt['variablesource']}\"")

    elif "datasource" in stmt:
        # rs: RetStruct
        rs = session.data_source_manager.query(
            stmt["datasource"], pattern, session.session_id, session.store, limit
        )
        query_id = rs.load_to_store(session.store)
        session.store.extract(local_var_table, return_type, query_id, pattern)
        local_stage_varstruct = new_var(
            session.store, local_var_table, [], stmt, session.symtable
        )
        _logger.debug(
            f"native GET pattern executed and DB view {local_var_table} extracted."
        )

        # TODO: add a ECGP method to do this directly
        pat_summary = summarize_pattern(pattern)

        local_stage_var_entity_id = get_entity_id_attribute(local_stage_varstruct)
        if (
            pat_summary
            and return_type in pat_summary  # allow extended subgraph
            and len(pat_summary[return_type]) == 1  # only one attr for center node
            and pat_summary[return_type].pop() == local_stage_var_entity_id
        ):
            _logger.debug("To skip prefetch for direct query")
            is_direct_query = True
        else:
            is_direct_query = False

        return_var_table = do_prefetch(
            local_var_table, local_stage_varstruct, session, stmt, not is_direct_query
        )

    else:
        raise KestrelInternalError(f"unknown type of source in {str(stmt)}")

    output = new_var(session.store, return_var_table, [], stmt, session.symtable)

    if not len(output):
        if not return_type.startswith("x-") and return_type not in (
            set(session.store.types()) | set(get_entity_types())
        ):
            display = DisplayWarning(f'unknown entity type "{return_type}"')

    return output, display


@_debug_logger
@_default_output
@_guard_empty_input
def find(stmt, session):
    # shortcuts
    return_type = stmt["type"]
    input_type = session.symtable[stmt["input"]].type
    local_var_table = stmt["output"] + "_local"

    # init
    rel_query = None
    return_var_table = None

    if return_type in session.store.types():
        input_var_attrs = session.store.columns(input_type)
        return_type_attrs = session.store.columns(return_type)

        # First, get information from local store
        if stmt["relation"] in generic_relations:
            rel_query = compile_generic_relation_to_query(
                return_type, input_type, session.symtable[stmt["input"]].entity_table
            )

        else:
            rel_query = compile_specific_relation_to_query(
                return_type,
                stmt["relation"],
                input_type,
                stmt["reversed"],
                stmt["input"],
                input_var_attrs,
                return_type_attrs,
            )

        # `session.store.assign_query` will generate new entity_table named `local_var_table`
        if rel_query:
            session.store.assign_query(local_var_table, rel_query, return_type)
            local_stage_varstruct = new_var(
                session.store, local_var_table, [], stmt, session.symtable
            )
            return_var_table = do_prefetch(
                local_var_table, local_stage_varstruct, session, stmt
            )

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


def _build_query(store, entity_table, qry, stmt, paths=None):
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
    if attrs == "*" and not qry.joins:
        # If user didn't ask for any paths and the where clause didn't
        # result in any joins, fallback to the calling function's list
        # of paths.
        # https://github.com/opencybersecurityalliance/kestrel-lang/issues/312
        cols = paths
    else:
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


def _transform_query(store, entity_table, transform):
    if transform.lower() == "timestamped":
        qry = store.timestamped(entity_table, run=False)
    elif transform.lower() == "addobsid":
        qry = store.extract_observeddata_attribute(
            entity_table, name_of_attribute="id", run=False
        )
    elif transform.lower() == "records":
        qry = store.extract_observeddata_attribute(
            entity_table,
            name_of_attribute=[
                "number_observed",
                "first_observed",
                "last_observed",
                "id",
            ],
            run=False,
        )
    else:
        qry = Query(entity_table)
    return qry
