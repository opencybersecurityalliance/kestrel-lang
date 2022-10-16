import datetime
from abc import ABC, abstractmethod
from firepit.query import Filter, Predicate
from firepit.timestamp import timefmt
from kestrel.syntax.utils import merge_timeranges
from kestrel.syntax.reference import (
    Reference,
    deref_and_flatten_value_to_list,
    value_to_stix,
)
from kestrel.exceptions import (
    KestrelNotImplemented,
    InvalidECGPattern,
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

    @abstractmethod
    def deref(self, deref_func):
        pass


class ExtCenteredGraphPattern(ExtCenteredGraphConstruct):
    def __init__(self, graph: ExtCenteredGraphConstruct):
        self.graph = graph
        self.timerange = None

    def add_center_entity(self, center_entity_type: str):
        self.center_entity_type = center_entity_type

    def to_stix(
        self,
        timerange: (datetime.datetime, datetime.datetime),
        timeadj: (datetime.timedelta, datetime.timedelta),
    ):
        # timerange: user-specified timerange from Kestrel command
        # timeadj: time adjustments for START and STOP
        if timerange:
            if not (
                len(timerange) == 2
                and isinstance(timerange[0], datetime.datetime)
                and isinstance(timerange[1], datetime.datetime)
            ):
                raise TypeError("timerange should be datetime tuple")
        if timeadj:
            if not (
                len(timeadj) == 2
                and isinstance(timeadj[0], datetime.timedelta)
                and isinstance(timeadj[1], datetime.timedelta)
            ):
                raise TypeError("timeadj should be timedelta tuple")

        try:
            inner = self.graph.to_stix(self.center_entity_type)
        except AttributeError:
            raise KestrelInternalError(
                "should run add_center_entity() before to_stix()"
            )

        body = "[" + inner + "]"

        if timerange:
            tr = timerange
        elif self.timerange:
            tr = self.timerange
            if timeadj:
                tr = (tr[0] + timeadj[0], tr[1] + timeadj[1])
        else:
            tr = None

        if tr:
            tr_stix = f" START t'{timefmt(tr[0])}' STOP t'{timefmt(tr[1])}'"
        else:
            tr_stix = ""

        return body + tr_stix

    def to_firepit(self):
        try:
            return Filter([self.graph.to_firepit(self.center_entity_type)])
        except AttributeError:
            raise KestrelInternalError(
                "should run add_center_entity() before to_firepit()"
            )

    def deref(self, deref_func, get_timerange_func):
        self.timerange = self.graph.deref(deref_func, get_timerange_func)


class ECGPJunction(ExtCenteredGraphConstruct):
    def __init__(
        self,
        relation: str,
        lhs: ExtCenteredGraphConstruct,
        rhs: ExtCenteredGraphConstruct,
    ):
        # relation: "AND" | "OR"
        self.lhs = lhs
        self.rhs = rhs
        relation = relation.upper()
        if relation == "AND":
            self.relation = "AND"
        elif relation == "OR":
            self.relation = "OR"
        else:
            raise KestrelInternalError("unsupported relation for ECGPJunction()")

    def to_stix(self, center_entity_type: str):
        return (
            "("
            + self.lhs.to_stix(center_entity_type)
            + f") {self.relation} ("
            + self.rhs.to_stix(center_entity_type)
            + ")"
        )

    def to_firepit(self, center_entity_type: str):
        return Predicate(
            self.lhs.to_firepit(center_entity_type),
            self.relation,
            self.rhs.to_firepit(center_entity_type),
        )

    def deref(self, deref_func, get_timerange_func):
        ltr = self.lhs.deref(deref_func, get_timerange_func)
        rtr = self.rhs.deref(deref_func, get_timerange_func)
        return merge_timeranges((ltr, rtr))


class ECGPComparison(ExtCenteredGraphConstruct):
    def __init__(self, entity_attribute: str, operator: str, value, entity_type=None):
        self.etype = entity_type
        self.attribute = entity_attribute
        self.op = operator.upper()
        self.value = value
        if isinstance(self.value, list):
            if self.op not in ("IN", "NOT IN"):
                raise InvalidECGPattern(
                    'a list should be paired with the operator "IN"'
                )
        elif not isinstance(self.value, Reference):
            if self.op in ("IN", "NOT IN"):
                raise InvalidECGPattern(
                    'inappropriately pair operator "IN" with literal'
                )

    def to_stix(self, center_entity_type: str):
        if not self.etype:
            self.etype = center_entity_type
        return f"{self.etype}:{self.attribute} {self.op} {value_to_stix(self.value)}"

    def to_firepit(self, center_entity_type: str):
        if self.etype and self.etype != center_entity_type:
            raise KestrelNotImplemented("firepit filtering on linked entities")
        return Predicate(self.attribute, self.op, self.value)

    def deref(self, deref_func, get_timerange_func):
        xs, tr = deref_and_flatten_value_to_list(
            self.value, deref_func, get_timerange_func
        )
        if len(xs) == 0:
            raise InvalidECGPattern("empty value after deref of {self.value}")
        elif len(xs) == 1:
            self.value = xs[0]
            if self.op == "IN":
                self.op = "="
            elif self.op == "NOT IN":
                self.op = "!="
        else:
            self.value = xs
            if self.op in ("=", "==", "IN"):
                self.op = "IN"
            elif self.op in ("!=", "NOT IN"):
                self.op = "NOT IN"
            else:
                raise InvalidECGPattern(
                    "operator {self.op} incompatible with value {self.value}"
                )
        return tr
