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


class ReferenceNotFound(KestrelError):
    pass


class DataSourceNotFound(KestrelError):
    pass


class DuplicatedVariable(KestrelError):
    pass


class DuplicatedReference(KestrelError):
    pass


class DuplicatedDataSource(KestrelError):
    pass


class DuplicatedSingletonInstruction(KestrelError):
    pass


class MultiInterfacesInGraph(KestrelError):
    pass


class MultiSourcesInGraph(KestrelError):
    pass


class LargerThanOneIndegreeInstruction(KestrelError):
    pass


class DanglingReferenceInFilter(KestrelError):
    pass


class DanglingFilter(KestrelError):
    pass


class DuplicatedReferenceInFilter(KestrelError):
    pass


class InvalidSerializedDatasourceInterfaceCacheCatalog(KestrelError):
    pass


class InevaluableInstruction(KestrelError):
    pass


class MappingParseError(KestrelError):
    pass


class InterfaceNotFound(KestrelError):
    pass


class InterfaceNameCollision(KestrelError):
    pass


class IRGraphMissingNode(KestrelError):
    pass


class DataSourceInterfaceNotFound(KestrelError):
    pass


class InvalidDataSourceInterfaceImplementation(KestrelError):
    pass


class ConflictingDataSourceInterfaceScheme(KestrelError):
    pass
