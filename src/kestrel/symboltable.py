from kestrel.codegen.data import dump_data_to_file
from kestrel.codegen.summary import get_variable_entity_count
from kestrel.syntax.parser import get_all_input_var_names


class VarStruct:
    # variable data structure in symbol table

    def __init__(
        self,
        store,
        entity_table,
        link_tables,
        statement,
        entity_type,
        dep_vars,
        data_source,
    ):
        self.store = store

        # pointer (name of table) to internal data path (currently a view in SQLite)
        self.entity_table = entity_table

        # pointers (names of tables) to join tables for future many-to-many relations
        self.link_tables = link_tables

        # entity/SCO type of the variable
        self.type = entity_type

        # how many entities/SCOs in the variable
        self.length = get_variable_entity_count(self)
        self.records_count = (
            self.store.count(self.entity_table) if self.entity_table else 0
        )

        # TODO: cache of attributes for fast code completion request
        self.attributes = []

        # dependent variables
        self.dependent_variables = dep_vars

        # statement that generates the variable
        self.birth_statement = statement

        self.data_source = data_source

    def get_entities(self):
        return self.store.lookup(self.entity_table) if self.entity_table else []

    def dump_to_file(self, file_path):
        dump_data_to_file(self.store, self.entity_table, file_path)

    def __len__(self):
        return self.length

    def __repr__(self):
        return str(
            {
                "store name": self.store.dbname,
                "entity table name": self.entity_table,
                "link table names": self.link_tables,
                "entity type": self.type,
                "#(entities)": self.length,
                "#(records)": self.records_count,
                "attributes": self.attributes,
                "dependent variables": self.dependent_variables,
                "birth statement": self.birth_statement,
                "associated data source": self.data_source,
            }
        )

    def __iter__(self):
        """Useful for converting VarStruct to dict"""
        for attr in [
            "entity_table",
            "link_tables",
            "birth_statement",
            "type",
            "dependent_variables",
            "data_source",
        ]:
            yield attr, getattr(self, attr)


def _get_entity_type(stmt, symtable, dep_vars):
    if "type" in stmt:
        return stmt["type"]
    else:
        dep_var_name = dep_vars[0]
        dep_var = symtable[dep_var_name]
        return dep_var.type


def _get_data_source(stmt, dep_var_names, symtable):
    data_source = None
    if stmt["command"] == "get" and "datasource" in stmt:
        data_source = stmt["datasource"]
    else:
        dep_var_datasources = [symtable[v].data_source for v in dep_var_names]
        for ds in dep_var_datasources:
            if ds:
                data_source = ds
                break
    return data_source


def new_var(store, entity_table, link_tables, statement, symtable):
    dep_vars = get_all_input_var_names(statement)
    entity_type = _get_entity_type(statement, symtable, dep_vars)
    data_source = _get_data_source(statement, dep_vars, symtable)
    return VarStruct(
        store, entity_table, link_tables, statement, entity_type, dep_vars, data_source
    )
