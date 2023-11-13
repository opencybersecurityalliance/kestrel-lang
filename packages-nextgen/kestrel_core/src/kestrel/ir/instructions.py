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


class IRNode(DataClassJSONMixin):
    pass


@dataclass
class Filter(IRNode):
    exp: Union[IntComparison, FloatComparison, StrComparison, ListComparison, BoolExp]
