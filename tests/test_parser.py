import re

from lark import UnexpectedToken
import pytest

from kestrel.syntax.parser import parse


def test_simple_get():
    results = parse("y = get url from udi://all where [url:value LIKE '%']")
    result = results[0]
    assert result["command"] == "get"
    assert result["type"] == "url"
    assert result["datasource"] == "udi://all"
    assert result["patternbody"] == "[url:value LIKE '%']"


def test_quoted_datasource():
    results = parse("y = get url from \"udi://My QRadar\" where [url:value LIKE '%']")
    result = results[0]
    assert result["command"] == "get"
    assert result["type"] == "url"
    assert result["datasource"] == "udi://My QRadar"
    assert result["patternbody"] == "[url:value LIKE '%']"


@pytest.mark.parametrize(
    "outvar, sco_type, ds, pat",
    [
        ("_my_var", "ipv4-addr", "something", "[ipv4-addr:value = '192.168.121.121']"),
        (
            "X1",
            "x-custom-object",
            "myscheme://foo.bar/whatever",
            "[x-other-custom-thing:x_custom_prop IN ('a', 'b', 'c']",
        ),
        (
            "urls",
            "url",
            "file:///shared-vol/udsstx",
            "[url:value LIKE 'https://%'] START t'2021-03-29T19:25:12.345Z' STOP t'2021-03-29T19:30:12.345Z'",
        ),
        (
            "ext_dns_conns",
            "network-traffic",
            '"udi://10k Traffic"',
            "[network-traffic:dst_port = 53 AND network-traffic:dst_ref.value NOT ISSUBSET '192.168.1.0/24']",
        ),
    ],
)
def test_parser_get(outvar, sco_type, ds, pat):
    patbody = re.sub(r" START .* STOP .*", "", pat)
    results = parse(f"{outvar} = GET {sco_type} FROM {ds} WHERE {pat}")
    result = results[0]
    assert result["output"] == outvar
    assert result["command"] == "get"
    assert result["type"] == sco_type
    assert result["datasource"] == ds.strip('"')  # We strip the double quotes
    assert result["patternbody"] == patbody


def test_apply_params():
    results = parse("apply xyz://my_analytic on foo with x=1, y=a,b,c")
    result = results[0]
    assert result["command"] == "apply"
    assert result["workflow"] == "xyz://my_analytic"
    assert result["inputs"] == ["foo"]
    assert result["parameter"] == {"x": 1, "y": ["a", "b", "c"]}


def test_apply_params_with_dots():
    results = parse("apply xyz://my_analytic on foo with x=0.1, y=a.value")
    result = results[0]
    assert result["command"] == "apply"
    assert result["workflow"] == "xyz://my_analytic"
    assert result["inputs"] == ["foo"]
    assert result["parameter"] == {"x": 0.1, "y": "a.value"}


def test_apply_params_with_decimal_and_dots():
    results = parse("apply xyz://my_analytic on foo with x=0.1, y=a.value,b,c")
    result = results[0]
    assert result["command"] == "apply"
    assert result["workflow"] == "xyz://my_analytic"
    assert result["inputs"] == ["foo"]
    assert result["parameter"] == {"x": 0.1, "y": ["a.value", "b", "c"]}


def test_apply_params_no_equals():
    with pytest.raises(UnexpectedToken):
        parse("apply xyz://my_analytic on foo with x=1, y")
