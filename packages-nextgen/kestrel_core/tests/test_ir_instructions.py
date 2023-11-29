import pytest

from kestrel.ir.instructions import (
    Variable,
    Source,
    get_instruction_class,
    instruction_from_dict,
    instruction_from_json,
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
    _id = v.id
    v.name = "qwer"
    assert v.id == _id


def test_stable_hash():
    s = Source("stixshifter://abc")
    h1 = hash(s)
    s.datasource = "abcd"
    h2 = hash(s)
    assert h1 == h2


def test_eq():
    s1 = Source("stixshifter://abc")
    s2 = Source("stixshifter://abc")
    s3 = instruction_from_dict(s1.to_dict())
    assert s1 != s2
    assert s1 == s3


def test_get_instruction_class():
    cls = get_instruction_class("Variable")
    v = cls("asdf")
    assert cls == Variable
    assert isinstance(v, Variable)


def test_add_source():
    s = Source("stixshifter://abc")
    j = s.to_dict()
    assert j["interface"] == "stixshifter"
    assert j["datasource"] == "abc"
    assert "id" in j
    assert "instruction" in j
    assert "uri" not in j
    assert "default_interface" not in j

    x = Source("abc", "stixshifter")
    assert x.interface == "stixshifter"
    assert x.datasource == "abc"

    with pytest.raises(InvalidDataSource):
        Source("sss://eee://ccc")

    with pytest.raises(InvalidDataSource):
        Source("sss")


def test_instruction_from_dict():
    v = Variable("asdf")
    d = v.to_dict()
    w = instruction_from_dict(d)
    assert w == v

    del d["id"]
    with pytest.raises(InvalidSeralizedInstruction):
        instruction_from_dict(d)


def test_instruction_from_json():
    v = Variable("asdf")
    j = v.to_json()
    w = instruction_from_json(j)
    assert w == v
