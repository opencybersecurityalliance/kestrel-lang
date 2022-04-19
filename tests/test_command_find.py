import json
import os
import pytest

from kestrel.session import Session


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


@pytest.fixture
def proc_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "doctored-1k.json")


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


def test_find_srcs(fake_bundle_file):
    with Session() as s:
        stmt = f"""
conns = get network-traffic
        from file://{fake_bundle_file}
        where [network-traffic:dst_port = 22]
srcs = FIND ipv4-addr CREATED conns
"""
        s.execute(stmt)
        srcs = s.get_variable("srcs")
        assert len(srcs) == 24


def test_find_file_linked_to_process(proc_bundle_file):
    with Session() as s:
        stmt = f"""
procs = get process
        from file://{proc_bundle_file}
        where [process:command_line LIKE 'wmic%']
files = FIND file LINKED procs
"""
        s.execute(stmt)
        procs = s.get_variable("procs")
        print(json.dumps(procs, indent=4))
        assert len(procs) == 7 * 3  # TEMP: 3 records per entity
        files = s.get_variable("files")
        print(json.dumps(files, indent=4))
        assert len(files) == 6  # TODO: double check this count


def test_find_file_loaded_by_process(proc_bundle_file):
    with Session() as s:
        stmt = f"""
procs = get process
        from file://{proc_bundle_file}
        where [process:command_line LIKE 'wmic%']
files = FIND file LOADED BY procs
"""
        s.execute(stmt)
        procs = s.get_variable("procs")
        print(json.dumps(procs, indent=4))
        assert len(procs) == 7 * 3  # TEMP: 3 records per entity
        files = s.get_variable("files")
        print(json.dumps(files, indent=4))
        assert len(files) == 1


def test_find_process_created_process(proc_bundle_file):
    with Session() as s:
        stmt = f"""
procs = get process
        from file://{proc_bundle_file}
        where [process:command_line LIKE 'wmic%']
parents = FIND process CREATED procs
"""
        s.execute(stmt)
        data = s.get_variable("parents")
        print(json.dumps(data, indent=4))
        assert len(data)


def test_find_refs_resolution_not_reversed_src_ref(proc_bundle_file):
    with Session() as s:
        stmt = f"""
nt = get network-traffic
     from file://{proc_bundle_file}
     where [network-traffic:src_port > 0]
p = FIND process CREATED nt
"""
        s.execute(stmt)
        p = s.get_variable("p")
        assert len(p) == 1897


def test_find_refs_resolution_reversed_src_ref(proc_bundle_file):
    with Session() as s:
        stmt = f"""
procs = get process
        from file://{proc_bundle_file}
        where [process:name LIKE '%']
conns = FIND network-traffic CREATED BY procs
"""
        s.execute(stmt)
        conns = s.get_variable("conns")
        assert (
            len(conns) == 853
        )  # FIXME: should be 948, I think (id collisions for network-traffic)

        # DISP with a ref (parent_ref) and ambiguous column (command_line)
        disp_out = s.execute("DISP procs ATTR name, parent_ref.name, command_line")
        data = disp_out[0].to_dict()["data"]
        print(json.dumps(data, indent=4))
