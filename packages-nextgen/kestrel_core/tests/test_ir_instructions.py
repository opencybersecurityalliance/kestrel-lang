import pytest

from kestrel.ir.instructions import (
    Variable,
    Source,
    get_instruction_class,
    instruction_from_dict,
    source_from_uri,
)
from kestrel.exceptions import (
    InvalidSeralizedInstruction,
    InvalidDataSource,
)


def test_instruction_post_init():
    v = Variable("asdf")
    j = v.to_dict()
    assert "id" in j
    assert "instruction" in j
    assert j["instruction"] == "Variable"


def test_stable_id():
    v = Variable("asdf")
    j = v.to_json()
    _id = v.id
    v.name = "qwer"
    assert v.id == _id


def test_get_instruction_class():
    cls = get_instruction_class("Variable")
    v = cls("asdf")
    assert cls == Variable
    assert isinstance(v, Variable)


def test_source_from_uri():
    s = source_from_uri("stixshifter://abc")
    j = s.to_dict()
    assert j["interface"] == "stixshifter"
    assert j["datasource"] == "abc"
    assert "uri" not in j

    x = source_from_uri("abc", "stixshifter")
    assert x.interface == "stixshifter"
    assert x.datasource == "abc"

    with pytest.raises(InvalidDataSource):
        source_from_uri("sss://eee://ccc")

    with pytest.raises(InvalidDataSource):
        source_from_uri("sss")


def test_instruction_from_dict():
    v = Variable("asdf")
    d = v.to_dict()
    w = instruction_from_dict(d)
    assert w == v

    del d["id"]
    with pytest.raises(InvalidSeralizedInstruction):
        instruction_from_dict(d)
