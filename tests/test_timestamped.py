import json
import os

import pytest

from kestrel.exceptions import MissingEntityAttribute
from kestrel.session import Session


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


def test_timestamped_disp(fake_bundle_file):
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
        out = s.execute("DISP TIMESTAMPED(conns)")
        data = out[0].to_dict()["data"]
        assert len(data) == 29
        assert "first_observed" in data[0]
        out = s.execute("DISP TIMESTAMPED(conns) LIMIT 5")
        data = out[0].to_dict()["data"]
        assert len(data) == 5
        assert "first_observed" in data[0]
        out = s.execute(
            "DISP TIMESTAMPED(conns) ATTR first_observed, src_ref.value, src_port"
        )
        data = out[0].to_dict()["data"]
        assert len(data) == 29
        assert "first_observed" in data[0]
        assert "src_ref.value" in data[0]
        assert "src_port" in data[0]
        assert "dst_ref.value" not in data[0]
        assert "dst_port" not in data[0]
        out = s.execute(
            "DISP TIMESTAMPED(conns) ATTR first_observed, src_ref.value, src_port LIMIT 5"
        )
        data = out[0].to_dict()["data"]
        assert len(data) == 5
        assert "first_observed" in data[0]
        assert "src_ref.value" in data[0]
        assert "src_port" in data[0]
        assert "dst_ref.value" not in data[0]
        assert "dst_port" not in data[0]


def test_timestamped_copy(fake_bundle_file):
    with Session() as s:
        stmt = f"""
ips = get ipv4-addr
      from file://{fake_bundle_file}
      where [ipv4-addr:value ISSUBSET '10.0.0.0/8']
ts = timestamped(ips)
"""
        s.execute(stmt)
        ips = s.get_variable("ts")
        print(json.dumps(ips, indent=4))
        assert len(ips) == 100


def test_timestamped_grouped_disp(fake_bundle_file):
    with Session() as s:
        stmt = f"""
conns = GET network-traffic
        FROM file://{fake_bundle_file}
	WHERE [network-traffic:dst_ref.value NOT ISSUBSET '192.168.0.0/16']
grp_conns = GROUP conns BY dst_ref.value WITH COUNT(dst_ref) AS count
DISP TIMESTAMPED(grp_conns)
"""
        with pytest.raises(MissingEntityAttribute) as e:
            s.execute(stmt)


def test_timestamped_grouped_assign(fake_bundle_file):
    with Session() as s:
        stmt = f"""
conns = GET network-traffic
        FROM file://{fake_bundle_file}
	WHERE [network-traffic:dst_ref.value NOT ISSUBSET '192.168.0.0/16']
grp_conns = GROUP conns BY dst_ref.value WITH COUNT(dst_ref) AS count
ts_grp_conns = TIMESTAMPED(grp_conns)
"""
        with pytest.raises(MissingEntityAttribute) as e:
            s.execute(stmt)
