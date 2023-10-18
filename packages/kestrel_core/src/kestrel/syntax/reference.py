import logging

from kestrel.exceptions import InvalidECGPattern

_logger = logging.getLogger(__name__)


class Reference:
    def __init__(self, variable, attribute):
        self.variable = variable
        self.attribute = attribute

    def __eq__(self, other):
        if self.variable == other.variable and self.attribute == other.attribute:
            return True
        else:
            return False

    def __str__(self):
        return "{" + self.variable + "." + self.attribute + "}"


def deref_and_flatten_value_to_list(value, deref_func, get_timerange_func):
    # always return a list of values, plus the time range: None or (start, end)
    if isinstance(value, Reference):
        tr = get_timerange_func(value)
        vs = deref_func(value)
        _logger.debug(f"derefed {value} to {vs} with extracted timerange {tr}")
        return vs, tr
    elif isinstance(value, list):
        xs = []
        start, end = None, None
        for x in value:
            vs, tr = deref_and_flatten_value_to_list(x, deref_func, get_timerange_func)
            xs.extend(vs)
            if tr:
                s, e = tr
                if start is None or s < start:
                    start = s
                if end is None or e > end:
                    end = e
        if start is None and end is None:
            timerange = None
        else:
            timerange = start, end
        return xs, timerange
    else:
        return [value], None


def value_to_stix(value):
    if isinstance(value, str):
        value = value.replace("\\", "\\\\")
        value = value.replace("'", "\\'")
        return "'" + value + "'"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (list, tuple)):
        return "(" + ",".join(map(value_to_stix, value)) + ")"
    elif isinstance(value, Reference):
        raise KestrelInternalError("reference should be derefed before value_to_stix()")
    else:
        raise InvalidECGPattern(f"invalid term: {value}")
