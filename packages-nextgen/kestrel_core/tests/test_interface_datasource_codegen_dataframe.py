import pytest
from pandas import DataFrame

from kestrel.interface.datasource.codegen.dataframe import (
    evaluate_source_instruction,
    evaluate_transforming_instruction,
)

from kestrel.ir.instructions import (
    Construct,
    Variable,
    Limit,
    ProjectAttrs,
)


def test_evaluate_Construct():
    data = [ {"name": "cmd.exe", "pid": 123}
           , {"name": "explorer.exe", "pid": 99}
           , {"name": "firefox.exe", "pid": 201}
           , {"name": "chrome.exe", "pid": 205}
           ]
    ins = Construct(data)
    df = evaluate_source_instruction(ins)
    assert df.equals(DataFrame(data))


def test_non_exist_eval():
    with pytest.raises(NotImplementedError):
        evaluate_transforming_instruction(Variable("asdf"), DataFrame())


def test_evaluate_Limit():
    data = [ {"name": "cmd.exe", "pid": 123}
           , {"name": "explorer.exe", "pid": 99}
           , {"name": "firefox.exe", "pid": 201}
           , {"name": "chrome.exe", "pid": 205}
           ]
    df = DataFrame(data)
    dfx = evaluate_transforming_instruction(Limit(2), df)
    assert dfx.equals(df.head(2))


def test_evaluate_ProjectAttrs():
    data = [ {"name": "cmd.exe", "pid": 123}
           , {"name": "explorer.exe", "pid": 99}
           , {"name": "firefox.exe", "pid": 201}
           , {"name": "chrome.exe", "pid": 205}
           ]
    df = DataFrame(data)
    dfx = evaluate_transforming_instruction(ProjectAttrs(["name"]), df)
    assert dfx.equals(df[["name"]])
