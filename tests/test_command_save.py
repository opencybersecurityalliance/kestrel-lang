import pytest
import os

from kestrel.session import Session


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


@pytest.fixture
def proc_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "doctored-1k.json")


def test_save_parquet_gz(tmp_path):
    save_path = tmp_path / "test_save_data.parquet.gz"
    data_file_path = os.path.join(
        os.path.dirname(__file__), "test_input_data_procs.parquet.gz"
    )
    with Session() as s:
        stmt_save = f"newvar = LOAD {data_file_path} SAVE newvar TO {save_path}"
        s.execute(stmt_save)
        assert save_path.exists()
        stmt_load = f"newload = LOAD {save_path}"
    with Session() as s:
        s.execute(stmt_load)
        v = s.get_variable("newload")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "reg.exe"


def test_save_network_traffic_v4(fake_bundle_file):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )
        session.execute("save conns to conns.csv")


def test_save_network_traffic_v4_v6(proc_bundle_file):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{proc_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )
        session.execute("save conns to conns.csv")
