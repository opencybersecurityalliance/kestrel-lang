from typing import (
    Union,
    Mapping,
)
from dataclasses import (
    dataclass,
    field,
)
from mashumaro.mixins.json import DataClassJSONMixin
import sys
import inspect
import uuid

from kestrel.ir.filter import (
    IntComparison,
    FloatComparison,
    StrComparison,
    ListComparison,
    BoolExp,
)

from kestrel.exceptions import (
    InvalidInstruction,
    InvalidSeralizedInstruction,
)


@dataclass
class Instruction(DataClassJSONMixin):
    id: uuid.UUID = field(init=False)
    instruction: str = field(init=False)

    def __post_init__(self):
        # stable id during Instruction lifetime
        self.id = uuid.uuid4()
        self.instruction = self.__class__.__name__

    def __hash__(self):
        # stable hash during Instruction lifetime
        return hash(self.id)


@dataclass
class Variable(Instruction):
    name: str
    deceased: bool = False


@dataclass
class Source(Instruction):
    uri: str
    interface: str


@dataclass
class Return(Instruction):
    pass


@dataclass
class Filter(Instruction):
    exp: Union[IntComparison, FloatComparison, StrComparison, ListComparison, BoolExp]


def get_instruction_class(name: str) -> Instruction:
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    instructions = [cls for _, cls in classes if issubclass(cls, Instruction)]
    try:
        return next(filter(lambda cls: cls.__name__ == name, instructions))
    except StopIteration:
        raise InvalidInstruction(name)


def instruction_from_dict(d: Mapping[str, Union[str, bool]]) -> Instruction:
    instruction_class = get_instruction_class(d["instruction"])
    try:
        instruction = instruction_class.from_dict(d)
    except:
        raise InvalidSeralizedInstruction(d)
    instruction.id = uuid.UUID(d["id"])
    return instruction
