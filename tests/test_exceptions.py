import os

import pytest

from kestrel.exceptions import KestrelSyntaxError
from kestrel.exceptions import VariableNotExist
from kestrel.session import Session


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


def test_unexpected_chars(fake_bundle_file):
    with Session(debug_mode=True) as session:
        with pytest.raises(KestrelSyntaxError) as einfo:
            session.execute(
                f"get ? network-traffic from file://{fake_bundle_file} where"
            )
        err = einfo.value
        assert err.line == 1
        assert err.column == 5
        assert err.expected == ["ENTITY_TYPE"]


def test_unexpected_token(fake_bundle_file):
    with Session(debug_mode=True) as session:
        with pytest.raises(KestrelSyntaxError) as einfo:
            session.execute(f"get from file://{fake_bundle_file} where")
        err = einfo.value
        assert err.line == 1
        assert err.column == 10
        assert set(err.expected) == set(["FROM", "WHERE"])


def test_unexpected_eol(fake_bundle_file):
    with Session(debug_mode=True) as session:
        with pytest.raises(KestrelSyntaxError) as einfo:
            session.execute(f"get process from file://{fake_bundle_file}")
        err = einfo.value
        assert err.line == 1
        assert err.column == 18
        assert err.expected == ["WHERE"]


def test_undefined_variable(fake_bundle_file):
    with Session(debug_mode=True) as session:
        with pytest.raises(VariableNotExist) as einfo:
            session.execute(f"get process from file://{fake_bundle_file} where pid=abc.pid")
        err = einfo.value
        assert err.var_name == 'abc'


def test_garbage():
    with Session(debug_mode=True) as session:
        with pytest.raises(KestrelSyntaxError) as einfo:
            session.execute("garbage")
        err = einfo.value
        assert err.expected == ["EQUAL"]
