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

class VariableNotExist(KestrelError):
    pass

class SourceNotExist(KestrelError):
    pass

class DuplicatedVariable(KestrelError):
    pass

class DuplicatedDataSource(KestrelError):
    pass

class MultiInterfacesInGraph(KestrelError):
    pass
