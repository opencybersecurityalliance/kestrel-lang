from kestrel.exceptions import InvalidECGPattern


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
        return self.variable + "." + self.attribute


def deref_and_flatten_value_to_list(value, deref_func):
    # always return a list
    if isinstance(value, Reference):
        return deref_func(value)
    elif isinstance(value, list):
        xs = []
        for x in value:
            xs.extend(deref_and_flatten_value_to_list(x, deref_func))
        return xs
    else:
        return [value]


def value_to_stix(value):
    if isinstance(value, str):
        return "'" + value + "'"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (list, tuple)):
        return "(" + ",".join(map(value_to_stix, value)) + ")"
    elif isinstance(value, Reference):
        raise KestrelInternalError("reference should be derefed before value_to_stix()")
    else:
        raise InvalidECGPattern(f"invalid term: {value}")
