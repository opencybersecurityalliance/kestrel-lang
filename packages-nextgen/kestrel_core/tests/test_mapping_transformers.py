import pandas as pd
import pytest

from kestrel.mapping.transformers import (
    run_transformer,
    run_transformer_on_series,
)


@pytest.mark.parametrize(
    "transform, value, expected", [
        ("dirname", r"C:\Windows\System32\cmd.exe", r"C:\Windows\System32"),
        ("basename", r"C:\Windows\System32\cmd.exe", r"cmd.exe"),
        ("startswith", r"C:\Windows\System32", r"C:\Windows\System32\%"),
        ("endswith", "cmd.exe", r"%\cmd.exe"),
        ("to_int", 1234, 1234),
        ("to_int", 1234.1234, 1234),  # Maybe this should fail?
        ("to_int", "1234", 1234),
        ("to_int", "0x4d2", 1234),
        ("to_str", "1234", "1234"),
        ("to_str", 1234, "1234"),
    ]
)
def test_run_transformer(transform, value, expected):
    assert run_transformer(transform, value) == expected


def test_run_series_basename():
    data = pd.Series([r"C:\Windows\System32\cmd.exe", r"C:\TMP"])
    result = list(run_transformer_on_series("basename", data))
    assert result == ["cmd.exe", "TMP"]
