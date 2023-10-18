"""The Kestrel code auto-complete function.

The `do_complete()` function provides a framework for auto-completion, which
makes implementing the auto-complete for each case straightforward.

One can add a solution to auto-complete each token in
`lark.exceptions.UnexpectedToken` in the `do_complete()` function. To
understand which tokens are expected after a code prefix, use the following
code:

.. highlight:: python

Example ::

    from kestrel.syntax.parser import parse_kestrel

    stmts = [ "a = b +"
            , "APPLY abc ON a, "
            , "DISP abc ATTR a, "
            ]

    for stmt in stmts:
        try:
            ast = parse_kestrel(stmt)
        except Exception as e:
            print(e)

To develop a solution for a new token to auto-complete, one can create a new
test case in `tests/test_completion.py` to verify the logic.

"""

import logging
from typeguard import typechecked
import re
import lark
import typing
from datetime import datetime

from kestrel.syntax.parser import parse_kestrel
from kestrel.symboltable.symtable import SymbolTable
from kestrel.datasource.manager import DataSourceManager
from kestrel.analytics.manager import AnalyticsManager
from kestrel.syntax.utils import (
    get_entity_types,
    get_keywords,
    all_relations,
)
from firepit.timestamp import timefmt

_logger = logging.getLogger(__name__)

ISO_TS_RE = re.compile(r"\d{4}(-\d{2}(-\d{2}(T\d{2}(:\d{2}(:\d{2}Z?)?)?)?)?)?")


@typechecked
def do_complete(
    code: str,
    cursor_pos: int,
    datasource_manager: DataSourceManager,
    analytics_manager: AnalyticsManager,
    symtable: SymbolTable,
) -> typing.Iterable[str]:
    _logger.debug("auto_complete function starts...")

    # do not care code after cursor position in the current version
    line = code[:cursor_pos]
    _logger.debug(f"line to auto-complete: {line}")

    # if the last char is a space, `line_to_parse = line`
    # otherwise, exclude the last token in `line_to_parse` to prompt the expected token
    last_word_prefix, line_to_parse = _split_last_token(line)
    _logger.debug(f"last word prefix: {last_word_prefix}")
    _logger.debug(f"line to parse: {line_to_parse}")

    try:
        ast = parse_kestrel(line_to_parse)

    except lark.exceptions.UnexpectedCharacters as e:
        suggestions = ["% illegal char in huntflow %"]
        _logger.debug(f"illegal character in `line_to_parse`, err: {str(e)}")

    except lark.exceptions.UnexpectedEOF as e:
        suggestions = ["% EOF auto-complete internal error, report to developers %"]
        # https://github.com/lark-parser/lark/issues/791
        # Lark updates may break this, check if it is the case
        # no need to use KestrelInternalError; not to break huntflow execution
        _logger.debug(f"Lark with LALR should not give this error: {str(e)}")

    except lark.exceptions.UnexpectedToken as e:
        error_token = e.token
        expected_tokens = e.accepts or e.expected
        expected_values = []
        varnames = list(symtable.keys())
        keywords = set(get_keywords())
        for token in expected_tokens:
            _logger.debug("token: %s", token)
            if token == "VARIABLE":
                expected_values.extend(varnames)
            elif token == "ISOTIMESTAMP":
                if last_word_prefix:
                    if last_word_prefix.startswith("t'"):
                        ts_prefix = last_word_prefix[2:]
                        ts_complete = _do_complete_timestamp(ts_prefix)
                        exp_value = "t'" + ts_complete + "'"
                    else:
                        exp_value = _do_complete_timestamp(last_word_prefix)
                else:
                    exp_value = timefmt(datetime.now())
                expected_values.append(exp_value)
            elif token == "DATASRC_SIMPLE":
                _logger.debug("auto-complete data source")
                expected_values.extend(
                    _do_complete_interface(
                        last_word_prefix,
                        datasource_manager.schemes(),
                        datasource_manager.list_data_sources_from_scheme,
                    )
                )
            elif token == "ANALYTICS_SIMPLE":
                _logger.debug("auto-complete analytics")
                expected_values.extend(
                    _do_complete_interface(
                        last_word_prefix,
                        analytics_manager.schemes(),
                        analytics_manager.list_analytics_from_scheme,
                    )
                )
            elif token == "ENTITY_TYPE":
                expected_values.extend(get_entity_types())
            elif token == "RELATION":
                expected_values.extend(all_relations)
            elif token == "REVERSED":
                expected_values.append("BY")
            elif token == "EQUAL":
                expected_values.append("=")
            elif token == "ATTRIBUTE":
                # TODO: attribute completion
                # https://github.com/opencybersecurityalliance/kestrel-lang/issues/79
                _logger.debug(f"TODO: ATTRIBUTE COMPLETION")
            elif token == "ENTITY_ATTRIBUTE_PATH":
                # TODO: attribute completion
                # https://github.com/opencybersecurityalliance/kestrel-lang/issues/79
                _logger.debug(f"TODO: ATTRIBUTE COMPLETION")
            elif token == "COMMA":
                expected_values.append(",")
            elif token in keywords:
                if last_word_prefix and last_word_prefix.islower():
                    token = token.lower()
                expected_values.append(token)
            else:
                # token not handled
                continue
        expected_values = sorted(expected_values)
        _logger.debug(f"expected values: {expected_values}")

        # turn `expected_values` into `suggestions`
        _p = last_word_prefix
        _e = expected_values
        suggestions = [t[len(_p) :] for t in _e if t.startswith(_p)] if _p else _e
        suggestions = set(suggestions)
        suggestions.discard("")
        suggestions = list(suggestions)
        _logger.debug(f"suggestions: {suggestions}")

    else:
        suggestions = []

        # handle optional components
        if ast:
            last_stmt = ast[-1]
            if last_stmt["command"] in ["assign", "disp"]:
                if "where" not in last_stmt:
                    suggestions.append("WHERE")
                if last_stmt["command"] == "disp" and last_stmt["attrs"] == "*":
                    suggestions.append("ATTR")
                if "attribute" not in last_stmt:
                    suggestions.append("SORT")
                if "limit" not in last_stmt:
                    suggestions.append("LIMIT")
                if "offset" not in last_stmt:
                    suggestions.append("OFFSET")
            elif last_stmt["command"] == "find":
                if "where" not in last_stmt:
                    suggestions.append("WHERE")
                if not last_stmt["timerange"]:
                    suggestions.append("START")
            elif last_stmt["command"] == "get":
                if not last_stmt["timerange"]:
                    suggestions.append("START")
            elif last_stmt["command"] == "group":
                if "aggregations" not in last_stmt:
                    suggestions.append("WITH")
            elif last_stmt["command"] == "join":
                if "attribute_1" not in last_stmt:
                    suggestions.append("BY")
            elif last_stmt["command"] == "load":
                if not last_stmt["type"]:
                    suggestions.append("AS")
            elif last_stmt["command"] == "apply":
                if not last_stmt["arguments"]:
                    suggestions.append("WITH")

    return suggestions


@typechecked
def _end_with_blank_or_comma(s: str) -> bool:
    return s[-1] in [" ", "\t", "\n", "\r", "\f", "\v", ","] if s else True


@typechecked
def _split_last_token(s: str) -> typing.Tuple[str, str]:
    last = ""
    if not _end_with_blank_or_comma(s):
        while not _end_with_blank_or_comma(s):
            last = s[-1] + last
            s = s[:-1]
    return last, s


@typechecked
def _do_complete_timestamp(ts_prefix: str) -> str:
    valid_ts_formats = [
        "%Y",
        "%Y-%m",
        "%Y-%m-%d",
        "%Y-%m-%dT%H",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    ]
    matched = ISO_TS_RE.match(ts_prefix)
    if matched:
        for ts_format in valid_ts_formats:
            _logger.debug(f"Match timestamp {ts_prefix} with format {ts_format}")
            try:
                ts = datetime.strptime(matched.group(), ts_format)
            except:
                _logger.debug(f"Timestamp match failed")
            else:
                ts_complete = timefmt(ts)
                _logger.debug(f"Timestamp completed: {ts_complete}")
                break
        else:
            ts_complete = "% TS auto-complete internal error, report to developers %"
            # no need to use KestrelInternalError; not to break huntflow execution
            _logger.debug(
                f"TS auto-complete internal error: `valid_ts_formats` is incomplete"
            )
    else:
        ts_complete = "% illegal ISO 8601 timestamp prefix %"
        _logger.debug(f"illegal ISO 8601 timestamp prefix: {ts_prefix}")
    return ts_complete


def _do_complete_interface(
    last_word_prefix: str,
    schemes: typing.Iterable[str],
    list_names_from_scheme: typing.Callable,
) -> typing.Iterable[str]:
    if last_word_prefix and "://" in last_word_prefix:
        scheme, _ = last_word_prefix.split("://")
        if scheme in schemes:
            names = list_names_from_scheme(scheme)
            paths = [scheme + "://" + name for name in names]
            _logger.debug(f"auto-complete interface {scheme}: {paths}")
            expected_values = paths
    else:
        expected_values = [scheme + "://" for scheme in schemes]
    return expected_values
