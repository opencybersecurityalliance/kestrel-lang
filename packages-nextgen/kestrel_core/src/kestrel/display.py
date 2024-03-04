from typing import List, Union, Mapping
from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin
from pandas import DataFrame


@dataclass
class NativeQuery(DataClassJSONMixin):
    # which query language
    language: str
    # what query statement
    statement: str


@dataclass
class GraphletExplanation(DataClassJSONMixin):
    # serialized IRGraph
    graph: Mapping
    # data source query
    query: NativeQuery


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
