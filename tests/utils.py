import os
import pytest


@pytest.fixture
def set_empty_kestrel_config(tmp_path):
    config_file = tmp_path / "kestrel.yaml"
    os.environ["KESTREL_CONFIG"] = str(config_file.expanduser().resolve())
    with open(config_file, "w") as cf:
        cf.write("")
    yield None
    del os.environ["KESTREL_CONFIG"]


@pytest.fixture
def set_no_prefetch_kestrel_config(tmp_path):
    config_file = tmp_path / "kestrel.yaml"
    os.environ["KESTREL_CONFIG"] = str(config_file.expanduser().resolve())
    with open(config_file, "w") as cf:
        cf.write(
            """
prefetch:
  switch_per_command:
    get: false
    find: false
"""
        )
    yield None
    del os.environ["KESTREL_CONFIG"]
