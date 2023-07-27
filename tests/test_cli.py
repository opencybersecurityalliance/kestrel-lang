import pytest
import subprocess

from .utils import stixshifter_profile_lab101

@pytest.fixture()
def create_huntflow(tmp_path):
    huntflow = """
procs = GET process FROM stixshifter://lab101
        WHERE name = 'svchost.exe'
        START 2021-01-01T00:00:00Z STOP 2022-01-01T00:00:00Z
"""

    expected_result_lines = ["VARIABLE    TYPE  #(ENTITIES)  #(RECORDS)  directory*  file*  ipv4-addr*  ipv6-addr*  mac-addr*  network-traffic*  process*  user-account*  x-ecs-destination*  x-ecs-network*  x-ecs-process*  x-ecs-source*  x-ecs-user*  x-oca-asset*  x-oca-event*", "   procs process          389        1066        1078   1114        3190        1910       1066              1014       725           1062                2016            2016            2120           2024         2124          1066          2132"]

    huntflow_file = tmp_path / "hunt101.hf"

    with open(huntflow_file, "w") as hf:
        hf.write(huntflow)

    huntflow_file_path = str(huntflow_file.expanduser().resolve())

    return huntflow_file_path, expected_result_lines



def test_cli(create_huntflow, stixshifter_profile_lab101):

    huntflow_file_path, expected_result_lines = create_huntflow
    result = subprocess.run(args = ["kestrel", huntflow_file_path], 
                            universal_newlines = True,
                            stdout = subprocess.PIPE
                           )

    result_lines = result.stdout.splitlines()
    assert result_lines[-3] == expected_result_lines[0]
    assert result_lines[-2] == expected_result_lines[1]


def test_python_module_call(create_huntflow, stixshifter_profile_lab101):

    huntflow_file_path, expected_result_lines = create_huntflow
    result = subprocess.run(args = ["python", "-m", "kestrel", huntflow_file_path], 
                            universal_newlines = True,
                            stdout = subprocess.PIPE
                           )

    result_lines = result.stdout.splitlines()
    assert result_lines[-3] == expected_result_lines[0]
    assert result_lines[-2] == expected_result_lines[1]
