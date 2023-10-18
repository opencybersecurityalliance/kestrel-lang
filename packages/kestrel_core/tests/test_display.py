import pytest
import json

from kestrel.session import Session


def test_display_block_summary_to_json():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
             , {"type": "process", "name": "explorer.exe", "pid": "99"}
             ]
"""
        d = s.execute(stmt)
    correct_json = json.loads(
        '{"display": "execution summary", "data": {"variables updated": [{"VARIABLE": "newvar", "TYPE": "process", "#(ENTITIES)": 2, "#(RECORDS)": 2, "process*": 0}], "footnotes": ["*Number of related records cached."]}}'
    )
    output_json = json.loads(d[0].to_json())
    del output_json["data"]["execution time"]
    assert output_json == correct_json


def test_display_block_summary_to_dict():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
             , {"type": "process", "name": "explorer.exe", "pid": "99"}
             ]
"""
        d = s.execute(stmt)
    correct_dict = {
        "display": "execution summary",
        "data": {
            "variables updated": [
                {
                    "VARIABLE": "newvar",
                    "TYPE": "process",
                    "#(ENTITIES)": 2,
                    "#(RECORDS)": 2,
                    "process*": 0,
                }
            ],
            "footnotes": ["*Number of related records cached."],
        },
    }
    output_dict = d[0].to_dict()
    del output_dict["data"]["execution time"]
    assert output_dict == correct_dict


def test_display_block_summary_get_from_variable():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
             , {"type": "process", "name": "explorer.exe", "pid": "97"}
             , {"type": "process", "name": "explorer.exe", "pid": "98"}
             , {"type": "process", "name": "explorer.exe", "pid": "99"}
             ]
exp = GET process from newvar WHERE [process:name = 'explorer.exe']
"""
        d = s.execute(stmt)
    correct_dict = {
        "display": "execution summary",
        "data": {
            "variables updated": [
                {
                    "VARIABLE": "newvar",
                    "TYPE": "process",
                    "#(ENTITIES)": 4,
                    "#(RECORDS)": 4,
                    "process*": 0,
                },
                {
                    "VARIABLE": "exp",
                    "TYPE": "process",
                    "#(ENTITIES)": 3,
                    "#(RECORDS)": 3,
                    "process*": 0,
                },
            ],
            "footnotes": ["*Number of related records cached."],
        },
    }
    output_dict = d[0].to_dict()
    del output_dict["data"]["execution time"]
    assert output_dict == correct_dict
