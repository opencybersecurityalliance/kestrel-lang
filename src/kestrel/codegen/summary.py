from firepit.exceptions import InvalidAttr
from firepit.query import (
    Query,
    Projection,
    Table,
    Filter,
    Predicate,
    Count,
    Unique,
    Join,
)
from collections import OrderedDict
from kestrel.codegen.relations import get_entity_id_attribute
from kestrel.exceptions import KestrelInternalError


def gen_variable_summary(var_name, var_struct):
    """Generate summary dictionary for a variable.

    Args:

        variable (kestrel.symboltable.variable.VarStruct): The target variable.

    Returns:

        dict: ``str`` to ``str`` dict on the variable summary.

    """
    summary = OrderedDict()
    footnote = "*Number of related records cached."

    summary["VARIABLE"] = var_name
    summary["TYPE"] = var_struct.type
    summary["#(ENTITIES)"] = len(var_struct)
    summary["#(RECORDS)"] = var_struct.records_count

    query_ids = _get_variable_query_ids(var_struct)

    is_from_direct_datasource = False
    var_birth_cmd = var_struct.birth_statement["command"]
    if var_birth_cmd == "find" or (
        var_birth_cmd == "get" and "datasource" in var_struct.birth_statement
    ):
        is_from_direct_datasource = True

    for entity_type in var_struct.store.types():
        if entity_type not in ("identity", "observed-data"):
            count = 0

            if query_ids and is_from_direct_datasource:
                query = Query(
                    [
                        Table(entity_type),
                        Join("__contains", "id", "=", "target_ref"),
                        Join("__queries", "source_ref", "=", "sco_id"),
                        Filter([Predicate("query_id", "IN", query_ids)]),
                        Unique(),
                        Count(),
                    ]
                )
                result = var_struct.store.run_query(query).fetchall()
                count = result[0]["count"]
                if entity_type == var_struct.type and count:
                    count = count - len(var_struct)
                    if count < 0:
                        raise KestrelInternalError(
                            f"impossible count regarding variable {var_name} and type {entity_type}"
                        )

            summary[f"{entity_type}*"] = count

    return summary, footnote


def _get_variable_query_ids(variable):
    query_ids = []
    if variable.entity_table:
        query = Query()
        query.append(Table("__queries"))
        query.append(Join(variable.entity_table, "sco_id", "=", "id"))
        query.append(Projection(["query_id"]))
        query.append(Unique())
        try:
            rows = variable.store.run_query(query).fetchall()
            query_ids = [r["query_id"] for r in rows]
        except InvalidAttr:
            pass
    return query_ids


def get_variable_entity_count(variable):
    entity_count = 0
    if variable.entity_table:
        entity_id_attr = get_entity_id_attribute(variable)
        if entity_id_attr not in variable.store.columns(variable.entity_table):
            return 0
        entity_count = variable.store.count(variable.entity_table)
    return entity_count
