import logging
import re

from kestrel.exceptions import InvalidAttribute, VariableNotExist, UnsupportedRelation
from kestrel.codegen.relations import stix_2_0_ref_mapping, generic_relations

_logger = logging.getLogger(__name__)


def check_elements_not_empty(stmt):
    for k, v in stmt.items():
        if isinstance(v, str) and not v:
            raise KestrelInternalError(f'incomplete parser; empty value for "{k}"')


def get_entity_table(var_name, symtable):
    if var_name not in symtable:
        raise VariableNotExist(var_name)
    return symtable[var_name].entity_table


def get_entity_type(var_name, symtable):
    if var_name not in symtable:
        raise VariableNotExist(var_name)
    return symtable[var_name].type


def get_entity_len(var_name, symtable):
    if var_name not in symtable:
        raise VariableNotExist(var_name)
    return len(symtable[var_name])


def recognize_var_source(stmt, symtable):
    # parser doesn't understand whether a data source is a Kestrel var
    # this function differente a Kestrel variable source from a data source
    if "datasource" in stmt:
        source = stmt["datasource"]
        if source in symtable:
            stmt["variablesource"] = source
            del stmt["datasource"]


def complete_data_source(stmt, ds):
    if stmt["command"] == "get":
        if "variablesource" not in stmt and "datasource" not in stmt:
            if ds:
                stmt["datasource"] = ds


def normalize_attrs(stmt, v):
    props = []
    for attr in re.split(r",\s*", stmt["attrs"]):
        entity_type, _, prop = attr.rpartition(":")
        if entity_type and entity_type != v.type:
            raise InvalidAttribute(attr)
        props.append(prop)
    return ",".join(props)


def check_semantics_on_find(stmt, input_type):

    if stmt["command"] != "find":
        return

    # relation should be in lowercase after parsing by kestrel.syntax.parser
    relation = stmt["relation"]
    return_type = stmt["type"]

    (entity_x, entity_y) = (
        (input_type, return_type) if stmt["reversed"] else (return_type, input_type)
    )

    if (
        entity_x,
        relation,
        entity_y,
    ) not in stix_2_0_ref_mapping and relation not in generic_relations:
        raise UnsupportedRelation(entity_x, relation, entity_y)


def check_var_exists(var_name, symtable):
    if var_name not in symtable:
        raise VariableNotExist(var_name)
