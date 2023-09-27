from kestrel.exceptions import VariableNotExist


class SymbolTable(dict):
    def __getitem__(self, var_name):
        try:
            return super().__getitem__(var_name)
        except KeyError as e:
            raise VariableNotExist(var_name)
