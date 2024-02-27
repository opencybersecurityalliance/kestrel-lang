from __future__ import annotations

import copy
import inspect
import json
import sys
import uuid
from dataclasses import InitVar, dataclass, field, fields
from enum import Enum
from typing import Any, Iterable, List, Mapping, Optional, Type, Union

from kestrel.__future__ import is_python_older_than_minor_version
from kestrel.config.internal import CACHE_INTERFACE_IDENTIFIER
from kestrel.exceptions import (
    InvalidDataSource,
    InvalidInstruction,
    InvalidSeralizedInstruction,
)
from kestrel.ir.filter import (
    FExpression,
    ReferenceValue,
    TimeRange,
    get_references_from_exp,
    resolve_reference_with_function,
)
from mashumaro.mixins.json import DataClassJSONMixin
from typeguard import typechecked

# https://stackoverflow.com/questions/70400639/how-do-i-get-python-dataclass-initvar-fields-to-work-with-typing-get-type-hints
if is_python_older_than_minor_version(11):
    InitVar.__call__ = lambda *args: None


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

    def copy(self):
        return copy.copy(self)

    def deepcopy(self):
        return copy.deepcopy(self)

    def has_same_content_as(self, instruction: Instruction) -> bool:
        if self.instruction == instruction.instruction:
            flag = True
            for f in fields(self):
                if f.name != "id" and getattr(self, f.name) != getattr(
                    instruction, f.name
                ):
                    flag = False
        else:
            flag = False
        return flag


class TransformingInstruction(Instruction):
    """The instruction that builds/dependent on one or more instructions"""

    pass


class SolePredecessorTransformingInstruction(TransformingInstruction):
    """The translating instruction whose indegree==1"""

    pass


class SourceInstruction(Instruction):
    """The instruction that does not dependent on any instruction"""

    interface: str


class IntermediateInstruction(Instruction):
    """The instruction that aids AST to Kestrel IR compilation"""

    pass


@dataclass(eq=False)
class Return(SolePredecessorTransformingInstruction):
    """The sink instruction that forces execution

    Return is implemented as a TransformingInstruction so it triggers
    IRGraph._add_node_with_dependent_node() in IRGraph.add_node()
    """

    # the order/sequence of return instruction in huntflow (source code)
    sequence: int = 0


@dataclass(eq=False)
class Filter(TransformingInstruction):
    exp: FExpression
    timerange: TimeRange = field(default_factory=TimeRange)

    # TODO: from_json() for self.exp

    def get_references(self) -> Iterable[ReferenceValue]:
        return get_references_from_exp(self.exp)

    def resolve_references(self, f: Callable[[ReferenceValue], Any]):
        resolve_reference_with_function(self.exp, f)


@dataclass(eq=False)
class ProjectEntity(SolePredecessorTransformingInstruction):
    entity_type: str


@dataclass(eq=False)
class ProjectAttrs(SolePredecessorTransformingInstruction):
    # mashumaro does not support typing.Iterable, only List
    attrs: List[str]


@dataclass(eq=False)
class DataSource(SourceInstruction):
    uri: InitVar[Optional[str]] = None
    default_interface: InitVar[Optional[str]] = None
    interface: str = ""
    datasource: str = ""

    def __post_init__(self, uri: Optional[str], default_interface: Optional[str]):
        super().__post_init__()
        if uri:
            # normal constructor, not from deserliazation
            xs = uri.split("://")
            if len(xs) == 2:
                self.interface = xs[0]
                self.datasource = xs[1]
            elif len(xs) == 1 and default_interface:
                self.interface = default_interface
                self.datasource = xs[0]
            else:
                raise InvalidDataSource(uri)
        else:
            # from deserliazation; mashumaro will take care
            pass


@dataclass(eq=False)
class Variable(SolePredecessorTransformingInstruction):
    name: str
    # required to dereference a variable that has been created multiple times
    # the variable with the largest version will be used by dereference
    version: int = 0


@dataclass(eq=False)
class Reference(IntermediateInstruction):
    """Referred Kestrel variable (used in AST) before de-referencing to a Kestrel variable"""

    name: str


@dataclass(eq=False)
class Explain(SolePredecessorTransformingInstruction):
    pass


@dataclass(eq=False)
class Limit(SolePredecessorTransformingInstruction):
    num: int


@dataclass(eq=False)
class Offset(SolePredecessorTransformingInstruction):
    num: int


@dataclass(eq=False)
class Construct(SourceInstruction):
    data: List[Mapping[str, Union[str, int, bool]]]
    interface: str = CACHE_INTERFACE_IDENTIFIER


class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


@dataclass(eq=False)
class Sort(SolePredecessorTransformingInstruction):
    attribute: str
    direction: SortDirection = SortDirection.DESC


@typechecked
def get_instruction_class(name: str) -> Type[Instruction]:
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    instructions = [cls for _, cls in classes if issubclass(cls, Instruction)]
    try:
        return next(filter(lambda cls: cls.__name__ == name, instructions))
    except StopIteration:
        raise InvalidInstruction(name)


@typechecked
def instruction_from_dict(d: Mapping[str, Union[str, bool, int]]) -> Instruction:
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
