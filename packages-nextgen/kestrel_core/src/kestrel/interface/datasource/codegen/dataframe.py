import sys
import inspect
import re
import operator
import functools
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
from kestrel.ir.filter import (
    FExpression,
    BoolExp,
    MultiComp,
    TimeRange,
    StrCompOp,
    NumCompOp,
    ExpOp,
    ListOp,
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
    return _eval_Filter_exp(instruction.exp, dataframe)


def _eval_Filter_exp(exp: FExpression, dataframe: DataFrame):
    if isinstance(exp, BoolExp):
        bs = _eval_Filter_exp_BoolExp(exp, dataframe)
    elif isinstance(exp, MultiComp):
        bss = [xs for xs in _eval_Filter_exp(exp.comps, dataframe)]
        if exp.op == ExpOp.AND:
            bs = functools.reduce(lambda x,y: x & y, bss)
        elif exp.op == ExpOp.OR:
            bs = functools.reduce(lambda x,y: x | y, bss)
        else:
            raise NotImplementedError("unkown kestrel.ir.filter.ExpOp type")
    else:
        bs = _eval_Filter_exp_Comparison(exp, dataframe)
    return dataframe[bs]


def _eval_Filter_exp_BoolExp(boolexp: BoolExp, dataframe: DataFrame):
    if boolexp.op == ExpOp.AND:
        bs = _eval_Filter_exp(boolexp.lhs, dataframe) & _eval_Filter_exp(
            boolexp.rhs, dataframe
        )
    elif boolexp.op == ExpOp.AND:
        bs = _eval_Filter_exp(boolexp.lhs, dataframe) | _eval_Filter_exp(
            boolexp.rhs, dataframe
        )
    else:
        raise NotImplementedError("unkown kestrel.ir.filter.ExpOp type")
    return bs


def _eval_Filter_exp_Comparison(
    c: FExpression,
    dataframe: DataFrame,
):
    comp2func = {
        NumCompOp.EQ: operator.eq,
        NumCompOp.NEQ: operator.ne,
        NumCompOp.LT: operator.lt,
        NumCompOp.LE: operator.le,
        NumCompOp.GT: operator.gt,
        NumCompOp.GE: operator.ge,
        StrCompOp.EQ: operator.eq,
        StrCompOp.NEQ: operator.ne,
        StrCompOp.LIKE: lambda w, x: re.search(w.replace("%", ".*?"), x),
        StrCompOp.NLIKE: lambda w, x: not re.search(w.replace("%", ".*?"), x),
        StrCompOp.MATCHES: lambda w, x: re.search(w, x),
        StrCompOp.NMATCHES: lambda w, x: not re.search(w, x),
        ListOp.IN: lambda w, x: x in w,
        ListOp.NIN: lambda w, x: x not in w,
    }

    try:
        return dataframe[c.field].apply(functools.partial(comp2func[c.op](c.value)))
    except KeyError:
        raise NotImplementedError("unkown kestrel.ir.filter.*Op type")
