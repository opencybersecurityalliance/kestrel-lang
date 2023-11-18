from __future__ import annotations
from typeguard import typechecked
from typing import (
    Type,
    Union,
    Mapping,
    Optional,
)
from dataclasses import (
    dataclass,
    field,
)
from mashumaro.mixins.json import DataClassJSONMixin
import sys
import inspect
import uuid
import json

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

    def __eq__(self, other: Instruction):
        return self.id == other.id

    def __hash__(self):
        # stable hash during Instruction lifetime
        return self.id.int


@dataclass(eq=False)
class Variable(Instruction):
    name: str
    deceased: bool = False


@dataclass(eq=False)
class Source(Instruction):
    interface: str
    datasource: str


@dataclass(eq=False)
class Return(Instruction):
    pass


@dataclass(eq=False)
class Filter(Instruction):
    exp: Union[IntComparison, FloatComparison, StrComparison, ListComparison, BoolExp]


@typechecked
def get_instruction_class(name: str) -> Type[Instruction]:
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


@typechecked
def instruction_from_json(json_str: str) -> Instruction:
    instruction_in_dict = json.loads(json_str)
    return instruction_from_dict(instruction_in_dict)


@typechecked
def source_from_uri(uri: str, default_interface: Optional[str]=None) -> Source:
    xs = uri.split("://")
    if len(xs) == 2:
        return Source(xs[0], xs[1])
    elif len(xs) == 1 and default_interface:
        return Source(default_interface, xs[0])
    else:
        raise InvalidDataSource(uri)