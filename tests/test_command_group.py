import json
import logging
import os
import pytest
import pathlib
import shutil
import tempfile
import pandas as pd

from kestrel.session import Session


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


def test_group_srcref(fake_bundle_file):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute("src_grps = group conns by src_ref.value")
        assert "src_grps" in session.get_variable_names()
        src_grps = session.get_variable("src_grps")
        assert src_grps is not None


def test_group_src_dst(fake_bundle_file):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute(
            (
                "grps = group conns by src_ref.value, dst_ref.value"
            )
        )
        assert "grps" in session.get_variable_names()
        grps = session.get_variable("grps")
        assert grps is not None
        assert len(grps) == 94  # 94 unique src-dst pairs in test bundle


@pytest.mark.parametrize(
    "agg_func, attr, expected",
    [
        ("max", "dst_ref.value", "max_dst_ref.value"),
        ("count", "dst_ref.value", "count_dst_ref.value"),
        ("nunique", "dst_ref.value", "nunique_dst_ref.value"),
    ],
)
def test_group_srcref_agg(fake_bundle_file, agg_func, attr, expected):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute(
            (
                "src_grps = group conns by src_ref.value"
                f" with {agg_func}({attr})"
            )
        )
        assert "src_grps" in session.get_variable_names()
        src_grps = session.get_variable("src_grps")
        assert src_grps is not None
        assert expected in src_grps[0]


@pytest.mark.parametrize(
    "agg_func, attr, alias",
    [
        ("max", "dst_ref.value", "rand_value"),
        ("count", "dst_ref.value", "whatever"),
        ("nunique", "dst_ref.value", "unique_dests"),
    ],
)
def test_group_srcref_agg_alias(fake_bundle_file, agg_func, attr, alias):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute(
            (
                "src_grps = group conns by src_ref.value"
                f" with {agg_func}({attr}) as {alias}"
            )
        )
        assert "src_grps" in session.get_variable_names()
        src_grps = session.get_variable("src_grps")
        assert src_grps is not None
        assert alias in src_grps[0]


def test_group_nt_binned_timestamp(fake_bundle_file):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute("ts_conns = TIMESTAMPED(conns)")
        session.execute(("conns_per_min = group ts_conns by bin(first_observed, 1m)"
                         " with count(dst_port) as count"))
        hist = session.get_variable("conns_per_min")
        assert len(hist) == 5
        assert hist[0]["first_observed_bin"] == "2020-06-30T19:25:00Z"
        assert hist[0]["count"] == 20
        assert hist[4]["first_observed_bin"] == "2020-06-30T19:29:00Z"
        assert hist[4]["count"] == 16


def test_group_nt_binned_port(fake_bundle_file):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute(("port_hist = group conns by bin(src_port, 10000)"
                         " with count(src_port) as count"))
        hist = session.get_variable("port_hist")
        print(json.dumps(hist, indent=4))
        assert len(hist) == 3
        assert hist[0]["src_port_bin"] == 40000
        assert hist[0]["count"] == 4
        assert hist[1]["src_port_bin"] == 50000
        assert hist[1]["count"] == 69
        assert hist[2]["src_port_bin"] == 60000
        assert hist[2]["count"] == 27
