from firepit.query import (
    Column,
    Filter,
    Join,
    Predicate,
    Projection,
    Query,
    Table,
    Unique,
)

from kestrel.codegen.relations import stix_2_0_ref_mapping


def compile_specific_relation_to_query(
    return_type,
    relation,
    input_type,
    is_reversed,
    input_var_name,
    input_var_attrs,
    return_type_attrs,
):
    (entity_x, entity_y) = (
        (input_type, return_type) if is_reversed else (return_type, input_type)
    )

    stix_src_refs, stix_tgt_refs = stix_2_0_ref_mapping[(entity_x, relation, entity_y)]

    for ref_name in stix_src_refs:
        # if there are multiple options, use first one found in DB
        (var_attr, ret_attr) = (ref_name, "id") if is_reversed else ("id", ref_name)
        if ref_name.endswith("_refs"):
            query = _generate_reflist_query(input_var_name, ref_name, entity_y)
        elif var_attr in input_var_attrs and ret_attr in return_type_attrs:
            query = _generate_ref_query(
                input_var_name, input_type, var_attr, return_type, ret_attr
            )
        else:
            continue
        return query

    for ref_name in stix_tgt_refs:
        # if there are multiple options, use first one found in DB
        (var_attr, ret_attr) = ("id", ref_name) if is_reversed else (ref_name, "id")
        if ref_name.endswith("_refs"):
            query = _generate_reflist_query(input_var_name, ref_name, entity_x)
        elif var_attr in input_var_attrs and ret_attr in return_type_attrs:
            query = _generate_ref_query(
                input_var_name, input_type, var_attr, return_type, ret_attr
            )
        else:
            continue
        return query

    return None


def compile_generic_relation_to_query(return_type, input_type, input_var_name):
    return SQLQuery(
        f"""
SELECT DISTINCT sco.*
 FROM __contains c
  JOIN "{return_type}" sco
   ON sco.id = c.target_ref
 WHERE source_ref IN (
  SELECT source_ref
   FROM __contains c
   WHERE target_ref LIKE '{return_type}--%'
  INTERSECT SELECT source_ref
   FROM __contains c
   WHERE target_ref LIKE '{input_type}--%')""",
        tuple(),
        input_var_name,
    )


# Utility class for overriding firepit behavior
# FIXME: A hack - need to figure out a btter way
class SQLQuery(Query):
    """A pre-written SQL query"""

    def __init__(self, query_text, query_values, var_name):
        super().__init__(var_name)
        self.text = query_text
        self.values = query_values

    def last_stage(self):
        return None

    def append(self, stage):
        raise NotImplementedError

    def render(self, placeholder):
        return self.text, self.values


def _generate_ref_query(input_var_name, input_type, var_attr, ret_type, ret_attr):
    # SELECT * FROM ret_type WHERE ret_type.ret_attr IN (SELECT var_attr FROM input_var_name)
    subq = Query(
        [
            Table(input_var_name),
            Projection([var_attr]),
        ]
    )
    return Query(
        [
            Table(ret_type),
            Filter([Predicate(ret_attr, "IN", subq)]),
        ]
    )


def _generate_reflist_query(input_var_name, ref_name, entity_y):
    return Query(
        [
            Table(input_var_name),
            Join("__reflist", "id", "=", "source_ref"),
            Join(entity_y, "target_ref", "=", "id"),
            Filter([Predicate("ref_name", "=", ref_name)]),
            Projection([Column("*", entity_y)]),  # All columns from entity_y
            Unique(),
        ]
    )
