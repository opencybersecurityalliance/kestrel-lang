import os
import pytest

from kestrel.session import Session


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


def test_return_table_not_exist(fake_bundle_file):
    with Session() as s:
        stmt = f"""
conns = get network-traffic
        from file://{fake_bundle_file}
        where [network-traffic:dst_port = 22]
procs = FIND process CREATED conns
"""
        summaries = s.execute(stmt)
    correct_dict = {
        "display": "execution summary",
        "data": {
            "variables updated": [
                {
                    "VARIABLE": "conns",
                    "TYPE": "network-traffic",
                    "#(ENTITIES)": 29,
                    "#(RECORDS)": 29,
                    "ipv4-addr*": 58,
                    "network-traffic*": 0,
                    "user-account*": 29,
                },
                {
                    "VARIABLE": "procs",
                    "TYPE": "process",
                    "#(ENTITIES)": 0,
                    "#(RECORDS)": 0,
                    "ipv4-addr*": 0,
                    "network-traffic*": 0,
                    "user-account*": 0,
                },
            ],
            "footnotes": ["*Number of related records cached."],
        },
    }
    output_dict = summaries[0].to_dict()
    del output_dict["data"]["execution time"]
    assert output_dict == correct_dict
