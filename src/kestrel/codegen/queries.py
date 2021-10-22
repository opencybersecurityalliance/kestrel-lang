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
    return_type, relation, input_type, is_reversed, input_var_name
):
    (entity_x, entity_y) = (
        (input_type, return_type) if is_reversed else (return_type, input_type)
    )

    stix_src_refs, stix_tgt_refs = stix_2_0_ref_mapping[(entity_x, relation, entity_y)]

    if stix_src_refs:
        # TODO: if there are multiple options, use first one found in DB
        ref_name = stix_src_refs[0]  # TEMP: only look at first
        if ref_name.endswith("_refs"):
            query = _generate_reflist_query(input_var_name, ref_name, entity_y)
        else:
            query = _generate_ref_query(input_var_name, ref_name, entity_y)
        return query

    if stix_tgt_refs:
        # TODO: if there are multiple options, use first one found in DB
        ref_name = stix_tgt_refs[0]  # TEMP: only look at first
        if ref_name.endswith("_refs"):
            query = _generate_reflist_query(input_var_name, ref_name, entity_x)
        else:
            query = _generate_ref_query(input_var_name, ref_name, entity_x)
        return query


def compile_generic_relation_to_query(return_type, input_type, input_var_name):
    return SQLQuery(
        f"""
SELECT sco.*
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
    )


# Utility class for overriding firepit behavior
# FIXME: A hack - need to figure out a btter way
class SQLQuery(Query):
    """A pre-written SQL query"""

    def __init__(self, query_text, query_values):
        self.stages = []  # For compatibility
        self.text = query_text
        self.values = query_values

    def last_stage(self):
        return None

    def append(self, stage):
        raise NotImplemented

    def render(self, placeholder):
        return self.text, self.values


def _generate_ref_query(input_var_name, ref_name, entity_y):
    return Query(
        [
            Table(input_var_name),
            Join(entity_y, ref_name, "=", "id"),
            Projection([Column("*", entity_y)]),  # All columns from entity_y
            Unique(),
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
