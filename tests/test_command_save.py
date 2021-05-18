import pytest
import os

from kestrel.session import Session


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
