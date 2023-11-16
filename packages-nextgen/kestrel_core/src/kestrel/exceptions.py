class KestrelError():
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

class SourceNotFound(KestrelError):
    pass

class DuplicatedVariable(KestrelError):
    pass

class DuplicatedDataSource(KestrelError):
    pass

class MultiInterfacesInGraph(KestrelError):
    pass
