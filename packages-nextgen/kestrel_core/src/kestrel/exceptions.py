class KestrelError(Exception):
    pass


class InstructionNotFound(KestrelError):
    pass


class InvalidInstruction(KestrelError):
    pass


class InvalidSeralizedGraph(KestrelError):
    pass


class InvalidSeralizedInstruction(KestrelError):
    pass


class InvalidDataSource(KestrelError):
    pass


class VariableNotFound(KestrelError):
    pass


class DataSourceNotFound(KestrelError):
    pass


class DuplicatedVariable(KestrelError):
    pass


class DuplicatedSourceInstruction(KestrelError):
    pass


class DuplicatedSingletonInstruction(KestrelError):
    pass


class MultiInterfacesInGraph(KestrelError):
    pass


class UnresolvedReference(KestrelError):
    pass


class InvalidSerializedDatasourceInterfaceCacheCatalog(KestrelError):
    pass
