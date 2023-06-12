import json
import logging
import os
import pytest
import pathlib
import shutil
import tempfile
import kestrel
import kestrel_datasource_stixshifter
import pandas as pd

from kestrel.session import Session


def get_df(session, var_name):
    return pd.DataFrame.from_records(session.get_variable(var_name))


def execute(session, script):
    result = session.execute(script)
    if isinstance(result, str):
        assert not result.startswith("[ERROR]")


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


@pytest.fixture
def fake_bundle_2():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle_2.json")


@pytest.fixture
def fake_bundle_3():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle_3.json")


@pytest.fixture
def cbcloud_powershell_bundle():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "powershell_search_stix_result.json")


def test_session_1(fake_bundle_file):
    with Session(debug_mode=True) as session:
        execute(
            session,
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where dst_port < 10000""",
        )
        conns = get_df(session, "conns")
        assert len(conns.index) == 100
        execute(session, "sort conns by dst_port asc")
        s = get_df(session, "_")
        assert len(s.index) == 100
        assert s.iloc[0]["dst_port"] == 22
        execute(session, "group conns by dst_port")
        s = get_df(session, "_")
        assert len(s.index) == 5
        port_3128 = s[(s["dst_port"] == 3128)]
        assert len(port_3128.index) == 1

        conns_sym = session.symtable["conns"]
        conns_dict = dict(conns_sym)
        assert conns_dict["type"] == conns_sym.type
        assert conns_dict["entity_table"] == conns_sym.entity_table


def test_session_timeframe(fake_bundle_file):
    with Session(debug_mode=True) as session:
        session = Session()
        script = f"""conns = get network-traffic
                     from file://{fake_bundle_file}
                     where [network-traffic:dst_port = 22] START t'2020-06-30T19:25:00.000Z' STOP t'2020-06-30T19:26:00.000Z'"""
        execute(session, script)
        conns = get_df(session, "conns")
        assert len(conns.index) == 7


@pytest.mark.parametrize(
    "sco_type, prop, op, value, count",
    [
        ("ipv4-addr", "value", "=", "'192.168.121.121'", 1),
        ("network-traffic", "src_ref.value", "=", "'192.168.121.121'", 1),
        ("network-traffic", "dst_port", "=", 22, 29),
        ("user-account", "account_login", "=", "'henry'", 1),
        ("user-account", "account_login", "LIKE", "'hen%'", 1),
        ("user-account", "account_login", "=", "'zane'", 0),
    ],
)
def test_session_simple(fake_bundle_file, sco_type, prop, op, value, count):
    with Session(debug_mode=True) as session:
        script = f"""result = get {sco_type} from file://{fake_bundle_file} where [{sco_type}:{prop} {op} {value}]"""
        execute(session, script)
        result = get_df(session, "result")
        assert len(result.index) == count


@pytest.mark.parametrize(
    "sco_type, pattern, count",
    [
        (
            "network-traffic",
            "[network-traffic:dst_ref.value = '10.0.0.91' AND network-traffic:dst_port = 22]",
            3,
        ),
        (
            "network-traffic",
            "[network-traffic:dst_ref.value = '10.0.0.91' OR network-traffic:dst_port = 22]",
            35,
        ),
    ],
)
def test_session_complex(fake_bundle_file, sco_type, pattern, count):
    with Session(debug_mode=True) as session:
        script = f"""result = get {sco_type} from file://{fake_bundle_file} where {pattern}"""
        execute(session, script)
        result = get_df(session, "result")
        assert len(result.index) == count


def test_generated_pattern(fake_bundle_file, fake_bundle_2):
    with Session(debug_mode=True) as session:
        script = f"""conns_a = get network-traffic
             from file://{fake_bundle_file}
         where [network-traffic:dst_ref.value = '10.0.0.134']"""
        execute(session, script)
        conns_a = get_df(session, "conns_a")
        script = f"""conns_b = get network-traffic
             from file://{fake_bundle_2}
         where [network-traffic:dst_port = conns_a.dst_port]"""
        execute(session, script)
        conns_b = get_df(session, "conns_b")
        conns_b.to_csv("conns_b.csv")
        # time range failed it
        assert len(conns_b.index) == 0
        assert os.path.exists("conns_b.csv")
        os.remove("conns_b.csv")


def test_generated_pattern_match(fake_bundle_file, fake_bundle_3):
    with Session(debug_mode=True) as session:
        script = f"""conns_a = get network-traffic
             from file://{fake_bundle_file}
         where [network-traffic:dst_ref.value = '10.0.0.134']"""
        execute(session, script)
        conns_a = get_df(session, "conns_a")
        script = f"""conns_b = get network-traffic
             from file://{fake_bundle_3}
         where [network-traffic:dst_port = conns_a.dst_port]"""
        execute(session, script)
        conns_b = get_df(session, "conns_b")
        conns_b.to_csv("conns_b.csv")
        # time range not tested since it is only generated for udi data sources
        assert len(conns_b.index) == 3
        # assert len(conns_b.index) == 2  # 2/3 matches due to time range
        assert os.path.exists("conns_b.csv")
        os.remove("conns_b.csv")


def test_disp_column_order(fake_bundle_file, caplog):
    #caplog.set_level(logging.DEBUG)
    with Session(debug_mode=True) as session:
        execute(
            session,
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port < 10000]""",
        )
        # SCO type in attr names should be optional
        recs = session.execute(f"disp conns attr src_port, dst_port")[0]
        conns = recs.dataframe
        print(conns.head())
        cols = conns.columns.to_list()
        assert cols.index("src_port") < cols.index("dst_port")

def test_get_set_variable(fake_bundle_file):
    with Session() as session:
        # Create a normal var
        script = f"x = get ipv4-addr from file://{fake_bundle_file} where [ipv4-addr:value = '192.168.121.121']"
        execute(session, script)
        var_list = session.get_variable_names()
        assert "x" in var_list
        var_x = session.get_variable("x")
        assert len(var_x) == 1
        val = var_x[0]
        assert val["type"] == "ipv4-addr"
        assert val["value"] == "192.168.121.121"

        # Now create a new var using Session API
        names = ["alice", "bob", "carol"]
        session.create_variable("y", names, object_type="user-account")
        var_list = session.get_variable_names()
        assert "x" in var_list
        assert "y" in var_list
        var_y = session.get_variable("y")
        assert len(var_y) == 3
        print(var_y)
        val = var_y[0]
        assert val["type"] == "user-account"
        # Maybe this should be 'account_login'?
        assert (
            val["user_id"] in names
        )  # Order is not preserved, so it could be any of these


def test_session_runtime_dir():
    # standard session
    with Session(debug_mode=False) as session:
        runtime_directory = session.runtime_directory
        runtime_master_dirctory = session._get_runtime_directory_master()

        assert os.path.exists(session.runtime_directory)

        # if not executed in a clean env; it has previous debug dirs
        if runtime_master_dirctory.exists():
            d = pathlib.Path(session.runtime_directory).resolve()
            d_master = runtime_master_dirctory.resolve()
            assert d != d_master

    assert not os.path.exists(session.runtime_directory)

    # debug session
    with Session(debug_mode=True) as session:
        runtime_directory = session.runtime_directory
        runtime_master_dirctory = session._get_runtime_directory_master()

        assert os.path.exists(runtime_directory)

    assert os.path.exists(runtime_directory)

    if runtime_master_dirctory.exists():
        d = pathlib.Path(runtime_directory).resolve()
        d_master = runtime_master_dirctory.resolve()
        assert d == d_master

    # predefined runtime_dir session managed by session
    d = pathlib.Path(tempfile.gettempdir()) / "kestrel-runtime-test"
    d = d.resolve()
    if os.path.exists(d):
        shutil.rmtree(d)
    with Session(runtime_dir=d) as session:
        session = Session()
        assert os.path.exists(d)
    assert not os.path.exists(d)

    # predefined runtime_dir session not managed by session
    d = pathlib.Path(tempfile.gettempdir()) / "kestrel-runtime-test"
    d = d.resolve()
    pathlib.Path(d).mkdir(parents=True, exist_ok=True)
    with Session(runtime_dir=d) as session:
        assert os.path.exists(d)
    assert os.path.exists(d)


def test_session_debug_from_env():
    os.environ["KESTREL_DEBUG"] = "something"
    with Session() as session:
        assert session.debug_mode == True


def test_sha256_attr_name(cbcloud_powershell_bundle):
    # Make sure we can handle single quotes in attr names
    with Session() as session:
        script = (
            "x = get process"
            f" from file://{cbcloud_powershell_bundle}"
            " where [process:name = 'powershell.exe']"
        )
        execute(session, script)
        out = session.execute("DISP x ATTR binary_ref.hashes.'SHA-256'")
        df = out[0].dataframe
        assert (
            df["binary_ref.hashes.'SHA-256'"][0]
            == "de96a6e69944335375dc1ac238336066889d9ffc7d73628ef4fe1b1b160ab32c"
        )


def test_disp_after_group(fake_bundle_file):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""
conns = get network-traffic from file://{fake_bundle_file}
    where [network-traffic:dst_port < 10000]
grouped = group conns by src_ref.value, dst_ref.value with count(src_ref.value) as count
"""
        )
        out = session.execute("DISP grouped ATTR src_ref.value, dst_ref.value, count")
        df = out[0].dataframe
        assert list(df.columns) == ["src_ref.value", "dst_ref.value", "count"]


def test_env_var_resolve(tmp_path):
    os.chdir(tmp_path)
    config_name = "abc.yaml"
    with open(config_name, "w") as config:
        config.write(r"""
language:
  default_variable: "_"
""")
    os.environ[kestrel.config.CONFIG_PATH_ENV_VAR] = config_name
    os.environ[kestrel_datasource_stixshifter.config.PROFILE_PATH_ENV_VAR] = config_name
    s = Session()
    full_path = os.path.join(os.getcwd(), config_name)
    assert os.environ[kestrel.config.CONFIG_PATH_ENV_VAR] == full_path 
    assert os.environ[kestrel_datasource_stixshifter.config.PROFILE_PATH_ENV_VAR] == full_path


def test_where_deref_network_traffic(fake_bundle_file):
    '''#290: expression does not work on attribute with reference'''
    with Session(debug_mode=True) as session:
        execute(
            session,
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port < 10000]""",
        )
        conns = get_df(session, "conns")
        assert len(conns.index) == 100
        execute(session, "c2 = conns where src_ref.value = '192.168.212.97'")
        c2 = session.get_variable("c2")
        assert len(c2) == 1
        assert c2[0]["dst_port"] == 22

        execute(session, "c2 = conns where src_ref.value = '192.168.121.121' and dst_ref.value = '10.0.0.134'")
        c2 = session.get_variable("c2")
        assert len(c2) == 1
        assert c2[0]["dst_port"] == 3128


def test_where_deref_process(cbcloud_powershell_bundle):
    '''#290: expression does not work on attribute with reference'''
    with Session() as session:
        script = (
            "x = get process"
            f" from file://{cbcloud_powershell_bundle}"
            " where [process:name = 'powershell.exe']"
        )
        execute(session, script)
        execute(session, "y = x where parent_ref.pid = 1544")
        y = session.get_variable("y")
        assert len(y) == 1
        assert y[0]["parent_ref.x_unique_id"] == "MYORGIDX-02629f16-00000608-00000000-1d71d10a09cc7c4"
