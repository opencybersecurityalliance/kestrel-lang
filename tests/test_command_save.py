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
    stmt_save = f"newvar = LOAD {data_file_path} SAVE newvar TO {save_path}"
    stmt_load = f"newload = LOAD {save_path}"

    with Session() as s:
        s.execute(stmt_save)
    assert save_path.exists()

    with Session() as s:
        s.execute(stmt_load)
        v = s.get_variable("newload")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "reg.exe"


def test_save_network_traffic_v4(tmp_path, fake_bundle_file):
    save_path = tmp_path / "conns.csv"
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = GET network-traffic
                        FROM file://{fake_bundle_file}
                        WHERE [network-traffic:dst_port > 0]""",
        )
        session.execute(f"SAVE conns TO {save_path}")
    assert save_path.exists()


def test_save_network_traffic_v4_v6(tmp_path, proc_bundle_file):
    save_path = tmp_path / "conns.csv"
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = GET network-traffic
                        FROM file://{proc_bundle_file}
                        WHERE [network-traffic:dst_port > 0]""",
        )
        session.execute(f"SAVE conns TO {save_path}")
    assert save_path.exists()
