from typeguard import typechecked
from typing import (
    Union,
    Mapping,
)
from dataclasses import (
    dataclass,
    field,
    InitVar,
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
    InvalidDataSource,
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
    uri: InitVar[str]
    interface: str = field(init=False)
    datasource: str = field(init=False)

    def __post_init__(self, uri):
        xs = uri.split("://")
        if len(xs) != 2:
            raise InvalidDataSource(uri)
        else:
            self.interface = xs[0]
            self.datasource = xs[1]


@dataclass
class Return(Instruction):
    pass


@dataclass
class Filter(Instruction):
    exp: Union[IntComparison, FloatComparison, StrComparison, ListComparison, BoolExp]


@typechecked
def get_instruction_class(name: str) -> Instruction:
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    instructions = [cls for _, cls in classes if issubclass(cls, Instruction)]
    try:
        return next(filter(lambda cls: cls.__name__ == name, instructions))
    except StopIteration:
        raise InvalidInstruction(name)


@typechecked
def instruction_from_dict(d: Mapping[str, Union[str, bool]]) -> Instruction:
    instruction_class = get_instruction_class(d["instruction"])
    try:
        instruction = instruction_class.from_dict(d)
        instruction.id = uuid.UUID(d["id"])
    except:
        raise InvalidSeralizedInstruction(d)
    else:
        return instruction
