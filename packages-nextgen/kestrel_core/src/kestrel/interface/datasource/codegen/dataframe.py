import sys
import inspect
from pandas import DataFrame
from typing import Callable

from kestrel.ir.instructions import (
    SourceInstruction,
    TransformingInstruction,
    Construct,
    Limit,
    ProjectAttrs,
    ProjectEntity,
    Filter,
)


def evaluate_source_instruction(instruction: SourceInstruction) -> DataFrame:
    eval_func = _select_eval_func(instruction.instruction)
    return eval_func(instruction)


def evaluate_transforming_instruction(
    instruction: TransformingInstruction, dataframe: DataFrame
) -> DataFrame:
    eval_func = _select_eval_func(instruction.instruction)
    return eval_func(instruction, dataframe)


def _select_eval_func(instruction_name: str) -> Callable:
    eval_funcs = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
    try:
        _funcs = filter(lambda x: x[0] == "_eval_" + instruction_name, eval_funcs)
        return next(_funcs)[1]
    except StopIteration:
        raise NotImplementedError(
            f"evaluation function for {instruction_name} in dataframe cache"
        )


def _eval_Construct(instruction: Construct):
    return DataFrame(instruction.data)


def _eval_Limit(instruction: Limit, dataframe: DataFrame):
    return dataframe.head(instruction.num)


def _eval_ProjectAttrs(instruction: ProjectAttrs, dataframe: DataFrame):
    return dataframe[instruction.attrs]


def _eval_ProjectEntity(instruction: ProjectEntity, dataframe: DataFrame):
    ...


def _eval_Filter(instruction: Filter, dataframe: DataFrame):
    ...
