import pytest
import os
import subprocess

@pytest.fixture()
def setup_huntflow(tmp_path):
    profiles = """
profiles:
    lab101:
        connector: stix_bundle
        connection:
            host: https://github.com/opencybersecurityalliance/data-bucket-kestrel/blob/main/stix-bundles/lab101.json?raw=true
        config:
            auth:
                username:
                password:
"""

    huntflow = """
procs = GET process FROM stixshifter://lab101
        WHERE name = 'svchost.exe'
        START 2021-01-01T00:00:00Z STOP 2022-01-01T00:00:00Z
"""

    expected_result_lines = ["VARIABLE    TYPE  #(ENTITIES)  #(RECORDS)  directory*  file*  ipv4-addr*  ipv6-addr*  mac-addr*  network-traffic*  process*  user-account*  x-ecs-destination*  x-ecs-network*  x-ecs-process*  x-ecs-source*  x-ecs-user*  x-oca-asset*  x-oca-event*", "   procs process          389        1066        1078   1114        3190        1910       1066              1014       725           1062                2016            2016            2120           2024         2124          1066          2132"]

    profile_file = tmp_path / "stixshifter.yaml"
    huntflow_file = tmp_path / "hunt101.hf"

    os.environ["KESTREL_STIXSHIFTER_CONFIG"] = str(profile_file.expanduser().resolve())
    with open(profile_file, "w") as pf:
        pf.write(profiles)

    with open(huntflow_file, "w") as hf:
        hf.write(huntflow)

    huntflow_file_path = str(huntflow_file.expanduser().resolve())

    # https://docs.pytest.org/en/latest/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization
    yield huntflow_file_path, expected_result_lines
    del os.environ["KESTREL_STIXSHIFTER_CONFIG"]



def test_cli(setup_huntflow):

    huntflow_file_path, expected_result_lines = setup_huntflow
    result = subprocess.run(args = ["kestrel", huntflow_file_path], 
                            universal_newlines = True,
                            stdout = subprocess.PIPE
                           )

    result_lines = result.stdout.splitlines()
    assert result_lines[-3] == expected_result_lines[0]
    assert result_lines[-2] == expected_result_lines[1]


def test_python_module_call(setup_huntflow):

    huntflow_file_path, expected_result_lines = setup_huntflow
    result = subprocess.run(args = ["python", "-m", "kestrel", huntflow_file_path], 
                            universal_newlines = True,
                            stdout = subprocess.PIPE
                           )

    result_lines = result.stdout.splitlines()
    assert result_lines[-3] == expected_result_lines[0]
    assert result_lines[-2] == expected_result_lines[1]
