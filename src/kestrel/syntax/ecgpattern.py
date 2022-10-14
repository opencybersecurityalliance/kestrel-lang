from abc import ABC, abstractmethod
from firepit.query import Filter, Predicate
from kestrel.exceptions import (
    KestrelNotImplemented,
    InvalidStixPattern,
    KestrelInternalError,
)


class ExtCenteredGraphConstruct(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def to_stix(self, center_entity_type: str):
        pass

    @abstractmethod
    def to_firepit(self, center_entity_type: str):
        pass


class ExtCenteredGraphPattern(ExtCenteredGraphConstruct):
    def __init__(self, graph: ExtCenteredGraphConstruct):
        self.graph = graph

    def add_center_entity(self, center_entity_type:str):
        self.center_entity_type = center_entity_type

    def to_stix(self):
        try:
            return self.graph.to_stix(self.center_entity_type)
        except AttributeError:
            raise KestrelInternalError("should run add_center_entity() before to_stix()")

    def to_firepit(self):
        try:
            return Filter([self.graph.to_firepit(self.center_entity_type)])
        except AttributeError:
            raise KestrelInternalError("should run add_center_entity() before to_firepit()")


class ECGPExpressionOr(ExtCenteredGraphConstruct):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def to_stix(self, center_entity_type: str):
        return (
            "("
            + self.lhs.to_stix(center_entity_type)
            + ") OR ("
            + self.rhs.to_stix(center_entity_type)
            + ")"
        )

    def to_firepit(self, center_entity_type: str):
        return Predicate(
            self.lhs.to_firepit(center_entity_type),
            "OR",
            self.rhs.to_firepit(center_entity_type),
        )


class ECGPExpressionAnd(ExtCenteredGraphConstruct):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def to_stix(self, center_entity_type: str):
        return (
            "("
            + self.lhs.to_stix(center_entity_type)
            + ") AND ("
            + self.rhs.to_stix(center_entity_type)
            + ")"
        )

    def to_firepit(self, center_entity_type: str):
        return Predicate(
            self.lhs.to_firepit(center_entity_type),
            "AND",
            self.rhs.to_firepit(center_entity_type),
        )


class ECGPComparison(ExtCenteredGraphConstruct):
    def __init__(self, entity_attribute: str, operator: str, value, entity_type=None):
        self.etype = entity_type
        self.attribute = entity_attribute
        self.op = operator
        self.value = value

    def deref_value(self, symboltable, store):
        # todo: implement it
        self.op = "IN"
        self.value = []

    def to_stix(self, center_entity_type: str):
        if not self.etype:
            self.etype = center_entity_type
        return f"{self.etype}:{self.attribute} {self.op} {value_to_stix(self.value)}"

    def to_firepit(self, center_entity_type: str):
        if self.etype and self.etype != center_entity_type:
            raise KestrelNotImplemented("firepit filtering on linked entities")
        return Predicate(self.attribute, self.op, self.value)


class Reference:
    def __init__(self, variable, attribute):
        self.variable = variable
        self.attribute = attribute

    def __eq__(self, other):
        if self.variable == other.variable and self.attribute == other.attribute:
            return True
        else:
            return False

    def to_string(self):
        return f"{self.variable}.{self.attribute}"


def value_to_stix(value):
    if isinstance(value, str):
        return "'" + value + "'"
    elif isinstance(value, (int, float)):
        return value
    elif isinstance(value, (list, tuple)):
        return "(" + ",".join(map(value_to_stix, value)) + ")"
    elif isinstance(value, Reference):
        raise KestrelInternalError("reference should be derefed before value_to_stix()")
    else:
        raise InvalidStixPattern(invalid_term_value=value)
