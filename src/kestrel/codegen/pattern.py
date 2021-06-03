import dateutil.parser
import datetime
import logging
import re

from kestrel.utils import dedup_dicts
from kestrel.semantics import get_entity_table
from kestrel.syntax.paramstix import parse_extended_stix_pattern
from kestrel.exceptions import (
    InvalidAttribute,
    UnsupportedStixSyntax,
    KestrelInternalError,
)
from firepit.exceptions import InvalidAttr

_logger = logging.getLogger(__name__)


def or_patterns(patterns):
    bodies = []
    time_range = []
    for pattern in patterns:
        if pattern:
            pieces = pattern.split()
            if len(pieces) > 4 and pieces[-4] == "START" and pieces[-2] == "STOP":
                time_range.append((pieces[-3], pieces[-1]))
                bodies.append("(" + " ".join(pieces[:-4]) + ")")
            else:
                bodies.append(pattern)
    if bodies:
        if time_range:
            start = min([t[0] for t in time_range])
            end = max([t[1] for t in time_range])
            final_pattern = (
                "(" + " OR ".join(bodies) + ")" + " START " + start + " STOP " + end
            )
        else:
            final_pattern = " OR ".join(bodies)
        _logger.debug(f"or pattern merged: {final_pattern}")
    else:
        final_pattern = None
        _logger.warning(f"all None patterns input into or_patterns()")

    return final_pattern


def build_pattern(
    raw_pattern_body, time_range, start_offset, end_offset, symtable, store
):
    """Dereference variables in a STIX pattern and output the unfolded pattern."""
    references = parse_extended_stix_pattern(raw_pattern_body)

    pattern_body = raw_pattern_body

    if references:
        _logger.debug(f"build pattern for: {raw_pattern_body}")
        _logger.debug(f"references found: {list(references.keys())}")

        var_attr_to_vals_str = _dereference_multiple_variables(
            store, symtable, references
        )
        for var_attr, vals_str in var_attr_to_vals_str.items():
            pattern_body = _replace_ref_with_op(pattern_body, var_attr, vals_str)

        _logger.debug(f'pattern body dereferred: "{pattern_body}"')

        if pattern_body and not time_range:
            try:
                ref_var_time_ranges = [
                    _get_variable_time_range(store, symtable, var_name)
                    for var_name in references.keys()
                ]

                start = min([t[0] for t in ref_var_time_ranges])
                end = max([t[1] for t in ref_var_time_ranges])

                start_adj = start + datetime.timedelta(seconds=start_offset)
                end_adj = end + datetime.timedelta(seconds=end_offset)

                start_stix = start_adj.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                stop_stix = end_adj.strftime("%Y-%m-%dT%H:%M:%S.000Z")

                time_range = (start_stix, stop_stix)
                _logger.debug(f"pattern time range computed: {time_range}")

            except InvalidAttribute:
                time_range = None
                _logger.warning(
                    f"pattern time range searching failed on variable {var_name}"
                )

    if pattern_body:
        if time_range:
            pattern = (
                f"({pattern_body}) START t'{time_range[0]}' STOP t'{time_range[1]}'"
            )
        else:
            pattern = f"{pattern_body}"
        _logger.debug(f'final pattern assembled: "{pattern}"')
    else:
        pattern = None
        _logger.warning(f"empty pattern assembled")

    return pattern


def _dereference_multiple_variables(store, symtable, references):
    return {
        var + "." + attr: "(" + ", ".join(map(_type_value, vals)) + ")"
        for var, attrs in references.items()
        for attr, vals in _dereference_variable(store, symtable, var, attrs).items()
    }


def _dereference_variable(store, symtable, var_name, attributes):
    attr_line = ",".join(attributes)
    _logger.debug(f'deref "{var_name}" with attributes "{attr_line}"')

    var_entity_table = get_entity_table(var_name, symtable)
    try:
        store_return = store.lookup(var_entity_table, attr_line)
    except InvalidAttr as e:
        raise InvalidAttribute(e.message)
    attr_to_values = {k: [] for k in attributes}
    for row in store_return:
        for k, v in row.items():
            if v and v not in attr_to_values[k]:
                attr_to_values[k].append(v)
    for k, v in attr_to_values.items():
        if not v:
            raise InvalidAttribute(var_name + "." + k)

    _logger.debug(f"deref results: {str(attr_to_values)}")

    return attr_to_values


def _get_variable_time_range(store, symtable, var_name):
    """
    Returns:
        start (datetime.datetime): the time any entities is observed first.
        end (datetime.datetime): the time any entities is observed last.

    """
    time_attr_line = ",".join(["first_observed", "last_observed"])
    var_entity_table = get_entity_table(var_name, symtable)
    try:
        store_return = store.lookup(var_entity_table, time_attr_line)
    except InvalidAttr as e:
        raise InvalidAttribute(e.message)
    life_span = dedup_dicts(store_return)
    start = min([dateutil.parser.isoparse(e["first_observed"]) for e in life_span])
    end = max([dateutil.parser.isoparse(e["last_observed"]) for e in life_span])
    return start, end


def _type_value(value):
    if isinstance(value, str):
        return f"'{value}'"
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        # pandas dataframe and sqlite may save integers as floats
        return str(round(value))
    else:
        return str(value)


def _replace_ref_with_op(pattern, var_attr, vals_str):

    # avoid adhesive parans/ops that prevent correct splitting
    pattern = re.sub(r"([=><\[\]])", r" \1 ", pattern)

    pieces = pattern.split()
    try:
        ref_index = pieces.index(var_attr)
    except ValueError:
        err_msg = f'cannot find "{var_attr}" when assembling pattern "{pattern}"'
        _logger.error(err_msg)
        raise KestrelInternalError(err_msg)
    if pieces[ref_index - 1] == "=":
        pieces[ref_index - 1] = "IN"
        pieces[ref_index] = vals_str
    else:
        raise UnsupportedStixSyntax(
            'only "=" is supported before referred variable in parameterized STIX'
        )
    return " ".join(pieces)
