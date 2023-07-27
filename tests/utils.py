import os
import pytest

# https://docs.pytest.org/en/latest/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization

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


@pytest.fixture
def stixshifter_profile_lab101(tmp_path):
    profile_file = tmp_path / "stixshifter.yaml"
    os.environ["KESTREL_STIXSHIFTER_CONFIG"] = str(profile_file.expanduser().resolve())
    with open(profile_file, "w") as pf:
        pf.write("""
profiles:
    lab101:
        connector: stix_bundle
        connection:
            host: https://github.com/opencybersecurityalliance/data-bucket-kestrel/blob/main/stix-bundles/lab101.json?raw=true
        config:
            auth:
                username:
                password:
""")
    yield None
    del os.environ["KESTREL_STIXSHIFTER_CONFIG"]
