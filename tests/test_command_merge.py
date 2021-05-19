import pytest

from kestrel.session import Session


def test_copy_and_merge():
    with Session() as s:
        stmt = """
newips = NEW ipv4-addr ["127.0.0.1", "127.0.1.15"]
ip2 = NEW ipv4-addr ["10.0.1.1", "10.0.2.2", "10.0.3.3"]
ip1 = newips
ip3 = ip1 + ip2
"""
        s.execute(stmt)
        newips = s.get_variable("newips")
        assert len(newips) == 2
        assert newips[0]["type"] == "ipv4-addr"
        values = [newips[i]["value"] for i in [0, 1]]
        values.sort()
        assert values == ["127.0.0.1", "127.0.1.15"]

        ip2 = s.get_variable("ip2")
        assert len(ip2) == 3
        assert ip2[0]["type"] == "ipv4-addr"
        values = [row["value"] for row in ip2]
        values.sort()
        assert values == ["10.0.1.1", "10.0.2.2", "10.0.3.3"]

        ip1 = s.get_variable("ip1")
        assert len(ip1) == 2
        assert ip1[0]["type"] == "ipv4-addr"
        values = [row["value"] for row in ip1]
        values.sort()
        assert values == ["127.0.0.1", "127.0.1.15"]

        ip3 = s.get_variable("ip3")
        assert len(ip3) == 5
        assert ip3[0]["type"] == "ipv4-addr"
        values = [row["value"] for row in ip3]
        values.sort()
        assert values == ["10.0.1.1", "10.0.2.2", "10.0.3.3", "127.0.0.1", "127.0.1.15"]
