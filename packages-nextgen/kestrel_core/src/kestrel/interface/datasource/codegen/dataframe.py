import sys
import inspect
import re
import operator
import functools
from typeguard import typechecked
from pandas import DataFrame, Series
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
from kestrel.ir.filter import (
    FExpression,
    BoolExp,
    MultiComp,
    StrCompOp,
    NumCompOp,
    ExpOp,
    ListOp,
)


@typechecked
def evaluate_source_instruction(instruction: SourceInstruction) -> DataFrame:
    eval_func = _select_eval_func(instruction.instruction)
    return eval_func(instruction)


@typechecked
def evaluate_transforming_instruction(
    instruction: TransformingInstruction, dataframe: DataFrame
) -> DataFrame:
    eval_func = _select_eval_func(instruction.instruction)
    return eval_func(instruction, dataframe)


@typechecked
def _select_eval_func(instruction_name: str) -> Callable:
    eval_funcs = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
    try:
        _funcs = filter(lambda x: x[0] == "_eval_" + instruction_name, eval_funcs)
        return next(_funcs)[1]
    except StopIteration:
        raise NotImplementedError(
            f"evaluation function for {instruction_name} in dataframe cache"
        )


@typechecked
def _eval_Construct(instruction: Construct) -> DataFrame:
    return DataFrame(instruction.data)


@typechecked
def _eval_Limit(instruction: Limit, dataframe: DataFrame) -> DataFrame:
    return dataframe.head(instruction.num)


@typechecked
def _eval_ProjectAttrs(instruction: ProjectAttrs, dataframe: DataFrame) -> DataFrame:
    return dataframe[instruction.attrs]


@typechecked
def _eval_ProjectEntity(instruction: ProjectEntity, dataframe: DataFrame) -> DataFrame:
    # TODO
    ...


@typechecked
def _eval_Filter(instruction: Filter, dataframe: DataFrame) -> DataFrame:
    return dataframe[_eval_Filter_exp(instruction.exp, dataframe)]


@typechecked
def _eval_Filter_exp(exp: FExpression, dataframe: DataFrame) -> Series:
    if isinstance(exp, BoolExp):
        bs = _eval_Filter_exp_BoolExp(exp, dataframe)
    elif isinstance(exp, MultiComp):
        bss = [xs for xs in _eval_Filter_exp(exp.comps, dataframe)]
        if exp.op == ExpOp.AND:
            bs = functools.reduce(lambda x, y: x & y, bss)
        elif exp.op == ExpOp.OR:
            bs = functools.reduce(lambda x, y: x | y, bss)
        else:
            raise NotImplementedError("unkown kestrel.ir.filter.ExpOp type")
    else:
        bs = _eval_Filter_exp_Comparison(exp, dataframe)
    return bs


@typechecked
def _eval_Filter_exp_BoolExp(boolexp: BoolExp, dataframe: DataFrame) -> Series:
    if boolexp.op == ExpOp.AND:
        bs = _eval_Filter_exp(boolexp.lhs, dataframe) & _eval_Filter_exp(
            boolexp.rhs, dataframe
        )
    elif boolexp.op == ExpOp.OR:
        bs = _eval_Filter_exp(boolexp.lhs, dataframe) | _eval_Filter_exp(
            boolexp.rhs, dataframe
        )
    else:
        raise NotImplementedError("unkown kestrel.ir.filter.ExpOp type")
    return bs


@typechecked
def _eval_Filter_exp_Comparison(
    c: FExpression,
    dataframe: DataFrame,
) -> Series:
    comp2func = {
        NumCompOp.EQ: operator.eq,
        NumCompOp.NEQ: operator.ne,
        NumCompOp.LT: operator.gt,  # value first in functools.partial
        NumCompOp.LE: operator.ge,  # value first in functools.partial
        NumCompOp.GT: operator.lt,  # value first in functools.partial
        NumCompOp.GE: operator.le,  # value first in functools.partial
        StrCompOp.EQ: operator.eq,
        StrCompOp.NEQ: operator.ne,
        StrCompOp.LIKE: lambda w, x: bool(
            re.search(w.replace(".", r"\.").replace("%", ".*?"), x)
        ),
        StrCompOp.NLIKE: lambda w, x: not bool(
            re.search(w.replace(".", r"\.").replace("%", ".*?"), x)
        ),
        StrCompOp.MATCHES: lambda w, x: bool(re.search(w, x)),
        StrCompOp.NMATCHES: lambda w, x: not bool(re.search(w, x)),
        ListOp.IN: lambda w, x: x in w,
        ListOp.NIN: lambda w, x: x not in w,
    }

    try:
        return dataframe[c.field].apply(functools.partial(comp2func[c.op], c.value))
    except KeyError:
        raise NotImplementedError(f"unkown kestrel.ir.filter.*Op type: {c.op}")
