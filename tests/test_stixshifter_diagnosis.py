import pytest
import subprocess

from kestrel_datasource_stixshifter.diagnosis import Diagnosis
from .utils import stixshifter_profile_lab101


def test_diagnosis(stixshifter_profile_lab101):
    pattern = " ".join([
        "[ipv4-addr:value LIKE '%']",
        "START t'2000-01-01T00:00:00.000Z' STOP t'3000-01-01T00:00:00.000Z'",
    ])
    diag = Diagnosis("lab101")
    diag.diagnose_config()
    diag.diagnose_ping()
    assert pattern == diag.diagnose_translate_query(pattern)["queries"][0]
    res = diag.diagnose_run_query_and_retrieval_result([pattern], 1)
    assert len(res) == 1 and res[0] == 533


def test_cli(stixshifter_profile_lab101):

    expected_output = """
## Diagnose: config verification

#### Kestrel specific config
retrieval batch size: 2000
cool down after transmission: 0
enable fast translation: False

#### Config to be passed to stix-shifter
connector name: stix_bundle
connection object [ref: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/OVERVIEW.md#connection]:
{
    "host": "https://github.com/opencybersecurityalliance/data-bucket-kestrel/blob/main/stix-bundles/lab101.json?raw=true",
    "options": {
        "result_limit": 4000,
        "timeout": 60
    }
}
configuration object [ref: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/OVERVIEW.md#configuration]:
{
    "auth": {
        "username": null,
        "password": null
    }
}

## Diagnose: stix-shifter to data source connection (network, auth)

#### Results from stixshifter transmission.ping()
{
    "success": true
}

## Diagnose: stix-shifter query translation

#### Input pattern
[ipv4-addr:value LIKE '%'] START t'2000-01-01T00:00:00.000Z' STOP t'3000-01-01T00:00:00.000Z'

#### Output data source native query
{
    "queries": [
        "[ipv4-addr:value LIKE '%'] START t'2000-01-01T00:00:00.000Z' STOP t'3000-01-01T00:00:00.000Z'"
    ]
}

## Diagnose: stix-shifter query execution: <=1 batch(s)

#### data retrieval results:
one batch retrieved: 533 entries

## Diagnose: stix-shifter query execution: <=5 batch(s)

#### data retrieval results:
one batch retrieved: 533 entries
"""

    result = subprocess.run(args = ["stix-shifter-diag", "lab101"], 
                            universal_newlines = True,
                            stdout = subprocess.PIPE
                           )

    result_lines = result.stdout.splitlines()
    result_lines = [x for x in result_lines if x]
    expected_lines = expected_output.splitlines()
    expected_lines = [x for x in expected_lines if x]
    for x,y in zip(result_lines, expected_lines):
        assert x == y
