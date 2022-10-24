import pytest
import pathlib
import os

from kestrel.session import Session
from kestrel.codegen.display import DisplayHtml


NEW_PROCS = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
             , {"type": "process", "name": "explorer.exe", "pid": "99"}
             ]
"""


REF_PROCS = """
ref = NEW [
          {"type": "process", "name": "", "pid": 4},
          {"type": "process", "name": "explorer.exe", "pid": 1380}
          ]
"""


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


@pytest.fixture
def fake_bundle_4():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle_4.json")


@pytest.fixture(autouse=True)
def env_setup(tmp_path):

    analytics_module_path = str(
        pathlib.Path(__file__).resolve().parent / "python_analytics_mockup.py"
    )

    profiles = f"""profiles:
    enrich_one_variable:
        module: {analytics_module_path}
        func: enrich_one_variable
    html_visualization:
        module: {analytics_module_path}
        func: html_visualization
    enrich_multiple_variables:
        module: {analytics_module_path}
        func: enrich_multiple_variables
    enrich_variable_with_arguments:
        module: {analytics_module_path}
        func: enrich_variable_with_arguments
    """

    profile_file = tmp_path / "pythonanalytics.yaml"
    with open(profile_file, "w") as pf:
        pf.write(profiles)

    os.environ["KESTREL_PYTHON_ANALYTICS_CONFIG"] = str(
        profile_file.expanduser().resolve()
    )


def test_enrich_one_variable():
    with Session() as s:
        s.execute(NEW_PROCS)
        s.execute("APPLY python://enrich_one_variable ON newvar")
        v = s.get_variable("newvar")
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert set([v[0]["x_new_attr"], v[1]["x_new_attr"]]) == set(
            ["newval0", "newval1"]
        )


def test_html_visualization():
    with Session() as s:
        s.execute(NEW_PROCS)
        displays = s.execute("APPLY python://html_visualization ON newvar")
        viz = displays[0]
        assert type(viz) is DisplayHtml
        assert viz.html == "<p>Hello World! -- a Kestrel analytics</p>"


def test_enrich_multiple_variables():
    with Session() as s:
        stmt = """
               v1 = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
                        , {"type": "process", "name": "explorer.exe", "pid": "99"}
                        ]
               v2 = NEW process ["cmd.exe", "explorer.exe", "google-chrome.exe"]
               v3 = NEW ipv4-addr ["1.1.1.1", "2.2.2.2"]
               APPLY python://enrich_multiple_variables ON v1, v2, v3
               """
        s.execute(stmt)

        v1 = s.get_variable("v1")
        assert set([v1[0]["x_new_attr"], v1[1]["x_new_attr"]]) == set(
            ["newval_a0", "newval_a1"]
        )

        v2 = s.get_variable("v2")
        assert set(
            [v2[0]["x_new_attr"], v2[1]["x_new_attr"], v2[2]["x_new_attr"]]
        ) == set(["newval_b0", "newval_b1", "newval_b2"])

        v3 = s.get_variable("v3")
        assert set([v3[0]["x_new_attr"], v3[1]["x_new_attr"]]) == set(
            ["newval_c0", "newval_c1"]
        )


def test_enrich_variable_with_arguments():
    with Session() as s:
        s.execute(NEW_PROCS)
        stmt = """
               APPLY python://enrich_variable_with_arguments
                     ON newvar
                     WITH argx=(abc,888), argy=123, argz="as\\"is"
               """
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["x_new_argx"] == "abc,888"
        assert v[0]["x_new_argy"] == '123'
        assert v[0]["x_new_argz"] == r'as"is'


def test_enrich_variable_with_reference_in_arguments():
    with Session() as s:
        s.execute(NEW_PROCS)
        s.execute(REF_PROCS)
        stmt = """
               APPLY python://enrich_variable_with_arguments
                     ON newvar
                     WITH argx=ref.pid, argy=123, argz=[ref.pid, 555]
               """
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["x_new_argx"] in ("4,1380", "1380,4")
        assert v[0]["x_new_argy"] == '123'
        assert v[0]["x_new_argz"] in ("4,1380,555", "1380,4,555")



def test_enrich_after_get_url(fake_bundle_file):
    with Session() as s:
        stmt = f"""
                newvar = get url
                         from file://{fake_bundle_file}
                         where value LIKE '%'
                APPLY python://enrich_one_variable ON newvar
                """
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 31
        assert v[0]["type"] == "url"
        assert "x_new_attr" in v[0]


def test_enrich_after_get_process(fake_bundle_4):
    with Session() as s:
        stmt = f"""
               newvar = get process
                        from file://{fake_bundle_4}
                        where binary_ref.name LIKE "%"
               APPLY python://enrich_one_variable ON newvar
               """
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 4
        assert v[0]["type"] == "process"
        assert "x_new_attr" in v[0]
