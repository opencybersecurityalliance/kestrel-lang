from typing import Union
from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

from kestrel.ir.filter import (
    IntComparison,
    FloatComparison,
    StrComparison,
    ListComparison,
    BoolExp,
)


class Instruction(DataClassJSONMixin):
    pass


@dataclass
class Filter(Instruction):
    exp: Union[IntComparison, FloatComparison, StrComparison, ListComparison, BoolExp]


@dataclass
class Source(Instruction):
    name: str


@dataclass
class Variable(Instruction):
    name: str
