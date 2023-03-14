# Python 3.10 supports this by default
# https://stackoverflow.com/questions/36286894/name-not-defined-in-type-annotation
from __future__ import annotations

from typeguard import typechecked

from typing import Tuple, Optional
import datetime
from abc import ABC, abstractmethod
from firepit.query import Column, Filter, Predicate, Query
from firepit.sqlstorage import get_path_joins
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


def _merge_queries(lhs: Query, op: str, rhs: Query):
    result = Query(lhs.table)
    result.joins = lhs.joins + rhs.joins
    lpred = lhs.where[0].preds[0]
    rpred = rhs.where[0].preds[0]
    result.where.append(Filter([Predicate(lpred, op, rpred)]))
    return result


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


@typechecked
class ExtCenteredGraphPattern(ExtCenteredGraphConstruct):
    def __init__(self, graph: ExtCenteredGraphConstruct):
        self.graph = graph
        self.timerange = None
        self.center_entity_type = None

    def __str__(self):
        return (
            f"graph: {self.graph}, "
            f"timerange: {self.timerange}, "
            f"center_entity_type: {self.center_entity_type}"
        )

    def add_center_entity(self, center_entity_type: str):
        self.center_entity_type = center_entity_type

    def prune_away_centered_graph(self, center_entity_type):
        # only leave the disconnected extended graph components
        if self.graph is not None:
            if_preserve_func = _make_extract_func(center_entity_type, "ext")
            self.graph = self.graph.prune(if_preserve_func)

    def prune_away_extended_graph(self, center_entity_type):
        # only leave the connected centered graph components
        if self.graph is not None:
            if_preserve_func = _make_extract_func(center_entity_type, "center")
            self.graph = self.graph.prune(if_preserve_func)

    def to_stix(
        self,
        timerange: Optional[Tuple[datetime.datetime, datetime.datetime]],
        timeadj: Optional[Tuple[datetime.timedelta, datetime.timedelta]],
    ):
        # timerange: user-specified timerange from Kestrel command
        # timeadj: time adjustments for START and STOP

        # before calling this, make sure:
        # 1. called deref()
        # 2. called add_center_entity()

        if self.center_entity_type is None:
            raise KestrelInternalError(
                "should run add_center_entity() before to_stix()"
            )

        if self.graph is None:
            inner = ""
        else:
            inner = self.graph.to_stix(self.center_entity_type)
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
        if self.center_entity_type is None:
            raise KestrelInternalError(
                "should run add_center_entity() before to_firepit()"
            )
        if self.graph is None:
            return None
        else:
            return self.graph.to_firepit(self.center_entity_type)

    def deref(self, deref_func, get_timerange_func):
        if self.graph is not None:
            self.timerange = self.graph.deref(deref_func, get_timerange_func)

    def extend(self, junction_type: str, other_ecgp: Optional[ExtCenteredGraphPattern]):
        if other_ecgp is not None and other_ecgp.graph is not None:
            if self.center_entity_type is None:
                self.center_entity_type = other_ecgp.center_entity_type
            elif other_ecgp.center_entity_type is None:
                pass
            elif self.center_entity_type != other_ecgp.center_entity_type:
                raise InvalidECGPattern(
                    "could not merge ECGPs with different center entities:"
                    + self.center_entity_type
                    + ", "
                    + other_ecgp.center_entity_type
                )

            self.timerange = merge_timeranges((self.timerange, other_ecgp.timerange))

            junction_type = junction_type.upper()

            if junction_type == "AND":
                self.graph = ECGPJunction("AND", self.graph, other_ecgp.graph)
            elif junction_type == "OR":
                self.graph = ECGPJunction("OR", self.graph, other_ecgp.graph)
            else:
                raise KestrelInternalError(
                    f'Junction type {junction_type} not supported besides "AND", "OR".'
                )


@typechecked
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

    def __str__(self):
        return f"({self.lhs}) {self.relation} ({self.rhs})"

    def prune(self, if_preserve_func):
        self.lhs = self.lhs.prune(if_preserve_func)
        self.rhs = self.rhs.prune(if_preserve_func)
        if self.lhs is None:
            return self.rhs
        elif self.rhs is None:
            return self.lhs
        else:
            return self

    def to_stix(self, center_entity_type: str):
        return (
            "("
            + self.lhs.to_stix(center_entity_type)
            + " "
            + self.relation
            + " "
            + self.rhs.to_stix(center_entity_type)
            + ")"
        )

    def to_firepit(self, center_entity_type: str):
        return _merge_queries(
            self.lhs.to_firepit(center_entity_type),
            self.relation,
            self.rhs.to_firepit(center_entity_type),
        )

    def deref(self, deref_func, get_timerange_func):
        ltr = self.lhs.deref(deref_func, get_timerange_func)
        rtr = self.rhs.deref(deref_func, get_timerange_func)
        return merge_timeranges((ltr, rtr))


@typechecked
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

    def __str__(self):
        return f"{self.etype}:{self.attribute} {self.op} {self.value}"

    def prune(self, if_preserve_func):
        if if_preserve_func(self.etype):
            return self
        else:
            return None

    def to_stix(self, center_entity_type: str):
        if not self.etype:
            self.etype = center_entity_type
        return f"{self.etype}:{self.attribute} {self.op} {value_to_stix(self.value)}"

    def to_firepit(self, center_entity_type: str):
        if self.etype and self.etype != center_entity_type:
            raise KestrelNotImplemented("firepit filtering on linked entities")
        joins, target_type, target_attr = get_path_joins(
            None, self.etype, self.attribute
        )
        if target_type:
            attribute = Column(target_attr, table=target_type)
        else:
            attribute = self.attribute
        qry = Query()
        qry.joins = joins
        qry.where = [Filter([Predicate(attribute, self.op, self.value)])]
        return qry

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


def _make_extract_func(center_entity_type, preserve_center_or_ext: str):
    def if_preserve_func(entity_type):
        if entity_type is None:
            connected_to_center = True
        elif entity_type == center_entity_type:
            connected_to_center = True
        else:
            connected_to_center = False

        if preserve_center_or_ext == "center":
            return connected_to_center
        elif preserve_center_or_ext == "ext":
            return not connected_to_center
        else:
            raise KestrelInternalError(
                "unsupported argument in _make_extract_func: {prune_center_or_ext}"
            )

    return if_preserve_func
