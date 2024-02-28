from typing import List, Union
from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin
from pandas import DataFrame


@dataclass
class GraphletExplanation(DataClassJSONMixin):
    # serialized IRGraph
    graph: dict
    # SQL/KQL query statement
    query: str


@dataclass
class GraphExplanation(DataClassJSONMixin):
    graphlets: List[GraphletExplanation]


# Kestrel Display Object
Display = Union[
    str,
    dict,
    DataFrame,
    GraphExplanation,
]
