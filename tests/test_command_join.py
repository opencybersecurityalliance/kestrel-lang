import os

from kestrel.session import Session


def test_join_csv_data():
    data_file_path = os.path.join(
        os.path.dirname(__file__), "test_input_data_ips.csv"
    )
    with Session() as s:
        s.execute(f"assets = LOAD {data_file_path} AS ipv4-addr")
        s.execute("""
ips = NEW [{"type": "ipv4-addr", "value": "192.168.1.2"},
           {"type": "ipv4-addr", "value": "192.168.1.3"}]
""")
        s.execute("risk_ips = JOIN ips, assets by value, value")
        v = s.get_variable("risk_ips")
        assert len(v) == 1
        assert v[0]["type"] == "ipv4-addr"
        assert v[0]["value"] == "192.168.1.2"
        assert v[0]["risk"] == 2
