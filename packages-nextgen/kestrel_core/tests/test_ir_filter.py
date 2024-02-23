import json

from kestrel.frontend.parser import parse_kestrel
from kestrel.ir.filter import (
    IntComparison, FloatComparison, StrComparison, ListComparison,
    RefComparison, ReferenceValue, ListOp, NumCompOp, StrCompOp, ExpOp,
    BoolExp, MultiComp, get_references_from_exp, resolve_reference_with_function,
)
from kestrel.ir.instructions import (
    Filter,
    instruction_from_json,
)

import pytest


@pytest.mark.parametrize(
    "field, op, value", [
        ("foo", StrCompOp.EQ, "bar"),
        ("foo", NumCompOp.EQ, 42),
        ("foo", NumCompOp.EQ, 3.14),
        ("foo", StrCompOp.NEQ, "bar"),
        ("foo", NumCompOp.NEQ, 42),
        ("foo", NumCompOp.NEQ, 3.14),
        ("foo", StrCompOp.LIKE, "%bar"),
        ("foo", StrCompOp.NLIKE, "%bar"),
    ]
)
def test_comparison(field, op, value):
    if isinstance(value, int):
        comp = IntComparison(field=field, op=op, value=value)
    elif isinstance(value, float):
        comp = FloatComparison(field=field, op=op, value=value)
    else:
        comp = StrComparison(field=field, op=op, value=value)
    assert comp.field == field
    assert comp.op == op
    assert comp.value == value
    json_data: str = comp.to_json()
    data: dict = json.loads(json_data)
    assert data["field"] == field
    assert data["op"] == op
    assert data["value"] == value
    if isinstance(value, int):
        comp2 = IntComparison.from_json(json_data)
    elif isinstance(value, float):
        comp2 = FloatComparison.from_json(json_data)
    else:
        comp2 = StrComparison.from_json(json_data)
    assert comp == comp2


@pytest.mark.parametrize(
    "field, op, value", [
        ("foo", ListOp.IN, ["a", "b", "c"]),
        ("foo", ListOp.NIN, ["a", "b", "c"]),
        ("foo", ListOp.IN, [1, 2, 3]),
        ("foo", ListOp.NIN, [1, 2, 3]),
    ]
)
def test_list_comparison(field, op, value):
    comp = ListComparison(field=field, op=op, value=value)
    assert comp.field == field
    assert comp.op == op
    assert comp.value == value
    json_data: str = comp.to_json()
    data: dict = json.loads(json_data)
    assert data["field"] == field
    assert data["op"] == op
    assert data["value"] == value
    comp2 = ListComparison.from_json(json_data)
    assert comp == comp2




def test_multi_comparison():
    comp1 = StrComparison("foo", StrCompOp.EQ, "X")
    comp2 = StrComparison("bar", StrCompOp.EQ, "Y")
    comp3 = StrComparison("baz", StrCompOp.EQ, "Z")
    mcomp = MultiComp(ExpOp.OR, [comp1, comp2, comp3])
    data = mcomp.to_json()
    mcomp2 = MultiComp.from_json(data)
    assert mcomp == mcomp2


@pytest.mark.parametrize(
    "lhs, op, rhs", [
        (StrComparison("foo", StrCompOp.EQ, "bar"), ExpOp.AND, IntComparison("baz", NumCompOp.EQ, 42)),
        (StrComparison("foo", StrCompOp.LIKE, "%bar%"), ExpOp.OR, IntComparison("baz", NumCompOp.LE, 42)),
        (IntComparison("baz", NumCompOp.GE, 42), ExpOp.AND, StrComparison("foo", StrCompOp.NEQ, "bar")),
        (IntComparison("baz", NumCompOp.NEQ, 42), ExpOp.OR, StrComparison("foo", StrCompOp.EQ, "bar")),
        (StrComparison("foo", StrCompOp.EQ, "bar"), ExpOp.AND, ListComparison("baz", ListOp.IN, ["a", "b", "c"])),
        (StrComparison("foo", StrCompOp.EQ, "bar"), ExpOp.OR, ListComparison("baz", ListOp.IN, [1, 2, 3])),
        (ListComparison("baz", ListOp.IN, ["a", "b", "c"]), ExpOp.AND, StrComparison("foo", StrCompOp.EQ, "bar")),
        (ListComparison("baz", ListOp.IN, [1, 2, 3]), ExpOp.OR, StrComparison("foo", StrCompOp.EQ, "bar")),
        (StrComparison("foo", StrCompOp.EQ, "X"), ExpOp.AND,
         MultiComp(ExpOp.OR, [StrComparison("bar", StrCompOp.EQ, "A"), StrComparison("baz", StrCompOp.EQ, "B")])),
    ]
)
def test_bool_exp(lhs, op, rhs):
    exp = BoolExp(lhs, op, rhs)
    data = exp.to_json()
    exp2 = BoolExp.from_json(data)
    assert exp == exp2

    # Also test Filter
    filt = Filter(exp)
    data = filt.to_json()
    filt2 = instruction_from_json(data)
    assert filt == filt2


def test_filter_compound_exp():
    comp1 = StrComparison("foo", StrCompOp.EQ, "bar")
    comp2 = IntComparison("baz", NumCompOp.EQ, 42)
    exp1 = BoolExp(comp1, ExpOp.AND, comp2)
    comp3 = StrComparison("thing1", StrCompOp.NEQ, "abc")
    comp4 = ListComparison("thing2", ListOp.IN, [1, 2, 3])
    exp2 = BoolExp(comp3, ExpOp.OR, comp4)
    exp3 = BoolExp(exp1, ExpOp.AND, exp2)
    filt = Filter(exp3)
    data = filt.to_json()
    filt2 = instruction_from_json(data)
    assert filt == filt2


def test_filter_with_reference():
    stmt = "x = y WHERE foo = 'bar' OR baz = z.baz"
    graph = parse_kestrel(stmt)
    filter_nodes = graph.get_nodes_by_type(Filter)
    exp = filter_nodes[0].exp
    exp_dict = exp.to_dict()
    assert exp_dict == {'lhs': {'field': 'foo', 'op': '=', 'value': 'bar'}, 'op': 'OR', 'rhs': {'field': 'baz', 'op': 'IN', 'value': {'reference': 'z', 'attribute': 'baz'}}}


def test_fill_references_in_exp():
    lhs = StrComparison("foo", StrCompOp.EQ, "bar")
    rhs = RefComparison("baz", "=", ReferenceValue("var", "attr"))
    exp = BoolExp(lhs, ExpOp.AND, rhs)
    rs = get_references_from_exp(exp)
    assert len(list(rs)) == 1
    resolve_reference_with_function(exp, lambda x: 5)
    assert exp.rhs.value == 5
