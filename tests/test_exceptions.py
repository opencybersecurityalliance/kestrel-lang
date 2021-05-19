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
        with pytest.raises(KestrelSyntaxError) as e:
            session.execute(
                "get ? network-traffic" f" from file://{fake_bundle_file}" " where"
            )
        print(e)


def test_unexpected_token(fake_bundle_file):
    with Session(debug_mode=True) as session:
        with pytest.raises(KestrelSyntaxError) as e:
            session.execute("get " f" from file://{fake_bundle_file}" " where")
        print(e)


def test_garbage():
    with Session(debug_mode=True) as session:
        with pytest.raises(VariableNotExist) as e:
            session.execute("garbage")
        print(e)
