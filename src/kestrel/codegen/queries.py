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
        # e.g., # STIX: ("process", "created", "network-traffic"): (["opened_connection_refs"], [])
        #       # type(p) == process; is_reversed == True
        #       nt = FIND network-traffic CREATED BY p
        #       # type(nt) == network-traffic; is_reversed == False
        #       p = FIND process CREATED nt
        #
        # It is just aligned that is_reversed == whether input_var is
        # - EntityX in stix_2_0_ref_mapping
        # - the source_ref in the __reflist table of firepit v2.0
        var_is_source = is_reversed

        (var_attr, ret_attr) = (ref_name, "id") if var_is_source else ("id", ref_name)

        # if there are multiple options, use first one found in DB
        if ref_name.endswith("_refs"):
            query = _generate_reflist_query(
                input_var_name, var_is_source, ref_name, return_type
            )

        elif var_attr in input_var_attrs and ret_attr in return_type_attrs:
            query = _generate_ref_query(
                input_var_name, input_type, var_attr, return_type, ret_attr
            )

        else:
            continue

        return query

    for ref_name in stix_tgt_refs:
        # e.g., # STIX: ("autonomous-system", "owned", "ipv4-addr"): ([], ["belongs_to_refs"])
        #       # type(a) == autonomous-system; is_reversed == True
        #       ip = FIND ipv4-addr OWNED BY a
        #       # type(ip) == ipv4-addr; is_reversed == False
        #       a = FIND autonomous-system OWNED ip
        #
        # It is just aligned that (not is_reversed) == whether input_var is
        # - EntityY in stix_2_0_ref_mapping
        # - the source_ref in the __reflist table of firepit v2.0
        var_is_source = not is_reversed

        (var_attr, ret_attr) = (ref_name, "id") if var_is_source else ("id", ref_name)

        # if there are multiple options, use first one found in DB
        if ref_name.endswith("_refs"):
            query = _generate_reflist_query(
                input_var_name, var_is_source, ref_name, return_type
            )

        elif var_attr in input_var_attrs and ret_attr in return_type_attrs:
            query = _generate_ref_query(
                input_var_name, input_type, var_attr, return_type, ret_attr
            )

        else:
            continue

        return query

    return None


def compile_generic_relation_to_query(return_type, input_type, input_var_table):
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
   WHERE target_ref IN (SELECT id FROM "{input_var_table}"))""",
        tuple(),
        input_var_table,
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

    def render(self, placeholder, dialect=None):
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


def _generate_reflist_query(input_var_name, var_is_source, ref_name, ret_type):
    var_ref_pos, ret_ref_pos = (
        ("source_ref", "target_ref") if var_is_source else ("target_ref", "source_ref")
    )
    return Query(
        [
            Table(input_var_name),
            Join("__reflist", "id", "=", var_ref_pos),
            Join(ret_type, ret_ref_pos, "=", "id"),
            Filter([Predicate("ref_name", "=", ref_name)]),
            Projection([Column("*", ret_type)]),  # All columns from ret_type
            Unique(),
        ]
    )
