import pytest
import os
import shutil

from kestrel.session import Session
from kestrel.exceptions import MissingEntityType


def test_load_full_csv():
    data_file_path = os.path.join(
        os.path.dirname(__file__), "test_input_data_procs.csv"
    )
    with Session() as s:
        stmt = f"newvar = LOAD {data_file_path}"
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "reg.exe"


def test_load_relative_path_csv(tmp_path):
    data_file_path = "test_input_data_procs.csv"
    ori_path = os.path.join(
        os.path.dirname(__file__), data_file_path
    )
    shutil.copy2(ori_path, tmp_path)
    os.chdir(tmp_path)
    with Session() as s:
        stmt = f"newvar = LOAD {data_file_path}"
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "reg.exe"


def test_load_full_json():
    data_file_path = os.path.join(
        os.path.dirname(__file__), "test_input_data_procs.json"
    )
    with Session() as s:
        stmt = f"newvar = LOAD {data_file_path}"
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "reg.exe"


def test_load_parquet_gz():
    data_file_path = os.path.join(
        os.path.dirname(__file__), "test_input_data_procs.parquet.gz"
    )
    with Session() as s:
        stmt = f"newvar = LOAD {data_file_path}"
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "reg.exe"


def test_load_notype_json_to_fail():
    data_file_path = os.path.join(
        os.path.dirname(__file__), "test_input_data_procs_no_type.json"
    )
    with Session() as s:
        stmt = f"newvar = LOAD {data_file_path}"
        with pytest.raises(MissingEntityType) as e:
            s.execute(stmt)


def test_load_notype_json_as_type():
    data_file_path = os.path.join(
        os.path.dirname(__file__), "test_input_data_procs_no_type.json"
    )
    with Session() as s:
        stmt = f"newvar = LOAD {data_file_path} AS process"
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "reg.exe"


def test_load_string_list_to_fail():
    data_file_path = os.path.join(
        os.path.dirname(__file__), "test_input_data_procs_list.json"
    )
    with Session() as s:
        stmt = f"newvar = LOAD {data_file_path}"
        with pytest.raises(MissingEntityType) as e:
            s.execute(stmt)


def test_load_string_list_as_type():
    data_file_path = os.path.join(
        os.path.dirname(__file__), "test_input_data_procs_list.json"
    )
    with Session() as s:
        stmt = f"newvar = LOAD {data_file_path} AS process"
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 3
        assert v[0]["type"] == "process"
        assert v[0]["name"] in ["cmd.exe", "reg.exe", "explorer.exe"]
        assert sorted([i["name"] for i in v]) == ["cmd.exe", "explorer.exe", "reg.exe"]
