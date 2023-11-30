# Lark Transformer

from datetime import datetime, timedelta
from functools import reduce

from dateutil.parser import parse as to_datetime
from lark import Transformer
from typeguard import typechecked

from kestrel.ir.filter import (
    IntComparison,
    FloatComparison,
    StrComparison,
    ListComparison,
    MultiComp,
    ListOp,
    NumCompOp,
    StrCompOp,
    ExpOp,
    BoolExp,
    TimeRange,
)
from kestrel.ir.graph import (
    IRGraph,
    compose,
)
from kestrel.ir.instructions import (
    Filter,
    Source,
    Limit,
    ProjectEntity,
    Variable,
)


DEFAULT_VARIABLE = "_"
DEFAULT_SORT_ORDER = "DESC"


@typechecked
def _unescape_quoted_string(s: str):
    if s.startswith("r"):
        return s[2:-1]
    else:
        return s[1:-1].encode("utf-8").decode("unicode_escape")


@typechecked
def _create_comp(field: str, op: str, value):
    if op in (ListOp.IN, ListOp.NIN):
        op = ListOp(op)
        comp = ListComparison(field=field, op=op, value=value)
    elif isinstance(value, int):
        op = NumCompOp(op)
        comp = IntComparison(field=field, op=op, value=value)
    elif isinstance(value, float):
        op = NumCompOp(op)
        comp = FloatComparison(field=field, op=op, value=value)
    else:
        op = StrCompOp(op)
        comp = StrComparison(field=field, op=op, value=value)
    return comp


def _map_filter_exp(entity_name, filter_exp, property_map):
    if isinstance(filter_exp, (IntComparison, FloatComparison, StrComparison,
                               ListComparison)):
        # get the field
        field = filter_exp.field
        # add entity to field if it doesn't have one already
        if ':' not in field:
            field = f"{entity_name}:{field}"
        # map field to new syntax (e.g. STIX to OCSF)
        map_result = property_map.get(field, field)
        # Build a MultiComp if field maps to several values
        if isinstance(map_result, (list, tuple)):
            op = filter_exp.op
            value = filter_exp.value
            filter_exp = MultiComp(
                ExpOp.OR,
                [_create_comp(field, op, value) for field in map_result]
            )
        else:  # change the name of the field if it maps to a single value
            filter_exp.field = map_result
    elif isinstance(filter_exp, BoolExp):
        # recursively map boolean expressions
        filter_exp = BoolExp(
            _map_filter_exp(entity_name, filter_exp.lhs, property_map),
            filter_exp.op,
            _map_filter_exp(entity_name, filter_exp.rhs, property_map)
        )
    elif isinstance(filter_exp, MultiComp):
        # normally, this should be unreachable
        # if this becomes a valid case, we need to change
        # the definition of MultiComp to accept a MultiComp
        # in addition to Comparisons in its `comps` list
        filter_exp = MultiComp(
            filter_exp.op,
            [_map_filter_exp(entity_name, x, property_map)
             for x in filter_exp.comps]
        )
    return filter_exp


class _KestrelT(Transformer):
    def __init__(
        self,
        default_variable=DEFAULT_VARIABLE,
        default_sort_order=DEFAULT_SORT_ORDER,
        token_prefix="",
        entity_map={},
        property_map={}
    ):
        # token_prefix is the modification by Lark when using `merge_transformers()`
        self.default_variable = default_variable
        self.default_sort_order = default_sort_order
        self.token_prefix = token_prefix
        self.entity_map = entity_map
        self.property_map = property_map
        super().__init__()

    def start(self, args):
        return reduce(compose, args, IRGraph())

    def statement(self, args):
        return args[0]

    def assignment(self, args):
        variable_node = Variable(args[0].value)
        graph, root = args[1]
        graph.add_node(variable_node, root)
        return graph

    def get(self, args):
        graph = IRGraph()
        entity_name = args[0].value
        mapped_entity_name = self.entity_map.get(entity_name, entity_name)
        filter = args[2]
        mapped_filter_exp = _map_filter_exp(args[0].value, filter.exp,
                                            self.property_map)
        source_node = graph.add_node(args[1])
        filter_node = graph.add_node(Filter(mapped_filter_exp), source_node)
        projection_node = graph.add_node(ProjectEntity(args[0].value), filter_node)
        root = projection_node
        if len(args) > 3:
            for arg in args[3:]:
                if isinstance(arg, TimeRange):
                    filter_node.timerange = args[3]
                elif isinstance(arg, Limit):
                    root = graph.add_node(arg, projection_node)
        return graph, root

    def where_clause(self, args):
        exp = args[0]
        return Filter(exp)

    def expression_or(self, args):
        return BoolExp(args[0], ExpOp.OR, args[1])

    def expression_and(self, args):
        return BoolExp(args[0], ExpOp.AND, args[1])

    def comparison_std(self, args):
        """Emit a Comparison object for a Filter"""
        field = args[0].value
        op = args[1]
        value = args[2]
        comp = _create_comp(field, op, value)
        return comp

    def op(self, args):
        """Convert operator token to a plain string"""
        return " ".join([arg.upper() for arg in args])

    def op_keyword(self, args):
        """Convert operator token to a plain string"""
        return args[0].value

    # Literals
    def advanced_string(self, args):
        value = _unescape_quoted_string(args[0].value)
        return value

    def number(self, args):
        v = args[0].value
        try:
            return int(v)
        except ValueError:
            return float(v)

    def value(self, args):
        return args[0]

    def literal_list(self, args):
        return args

    def literal(self, args):
        return args[0]

    def datasource(self, args):
        return Source(args[0].value)

    # Timespans
    def timespan_relative(self, args):
        num = int(args[0])
        unit = args[1]
        if unit == "DAY":
            delta = timedelta(days=num)
        elif unit == "HOUR":
            delta = timedelta(hours=num)
        elif unit == "MINUTE":
            delta = timedelta(minutes=num)
        elif unit == "SECOND":
            delta = timedelta(seconds=num)
        stop = datetime.utcnow()
        start = stop - delta
        return TimeRange(start, stop)

    def timespan_absolute(self, args):
        start = to_datetime(args[0])
        stop = to_datetime(args[1])
        return TimeRange(start, stop)

    def day(self, _args):
        return "DAY"

    def hour(self, _args):
        return "HOUR"

    def minute(self, _args):
        return "MINUTE"

    def second(self, _args):
        return "SECOND"

    def timestamp(self, args):
        return args[0]

    # Limit
    def limit_clause(self, args):
        n = int(args[0])
        return Limit(n)
