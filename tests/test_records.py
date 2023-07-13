import json
import os

import pytest

from kestrel.session import Session


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


def test_records_copy(fake_bundle_file):
    with Session() as s:
        stmt = f"""
ips = get ipv4-addr
      from file://{fake_bundle_file}
      where [ipv4-addr:value ISSUBSET '10.0.0.0/8']
ts = records(ips)
"""
        s.execute(stmt)
        ips = s.get_variable("ts")
        print(json.dumps(ips, indent=4))
        assert len(ips) == 100


def test_records_disp(fake_bundle_file):
    with Session() as s:
        stmt = f"""
conns = get network-traffic
        from file://{fake_bundle_file}
        where [network-traffic:dst_port = 22]
"""
        s.execute(stmt)
        out = s.execute("DISP conns")
        data = out[0].to_dict()["data"]
        assert len(data) == 29
        assert "first_observed" not in data[0]
        out = s.execute("DISP RECORDS(conns)")
        data = out[0].to_dict()["data"]
        assert len(data) == 29
        assert "number_observed" in data[0]
        assert "first_observed" in data[0]
        assert "last_observed" in data[0]
