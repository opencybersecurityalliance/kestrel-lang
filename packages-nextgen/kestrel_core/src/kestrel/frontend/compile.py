# Lark Transformer

from datetime import datetime, timedelta
from functools import reduce

from dateutil.parser import parse as to_datetime
from lark import Transformer, Token
from typeguard import typechecked

from kestrel.mapping.data_model import (
    reverse_mapping,
    translate_comparison_to_native,
    translate_comparison_to_ocsf,
)
from kestrel.utils import unescape_quoted_string
from kestrel.ir.filter import (
    FExpression,
    FComparison,
    IntComparison,
    FloatComparison,
    StrComparison,
    ListComparison,
    RefComparison,
    ReferenceValue,
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
    Construct,
    DataSource,
    Filter,
    Limit,
    Offset,
    ProjectAttrs,
    ProjectEntity,
    Reference,
    Return,
    Sort,
    Variable,
)
from kestrel.exceptions import IRGraphMissingNode


DEFAULT_VARIABLE = "_"
DEFAULT_SORT_ORDER = "DESC"


@typechecked
def _unescape_quoted_string(s: str):
    if s.startswith("r"):
        return s[2:-1]
    else:
        return s[1:-1].encode("utf-8").decode("unicode_escape")


@typechecked
def _create_comp(field: str, op_value: str, value) -> FComparison:
    if op_value in (ListOp.IN, ListOp.NIN):
        op = ListOp
        comp = RefComparison if isinstance(value, ReferenceValue) else ListComparison
    elif isinstance(value, int):
        op = NumCompOp
        comp = IntComparison
    elif isinstance(value, float):
        op = NumCompOp
        comp = FloatComparison
    elif isinstance(value, ReferenceValue):
        op = ListOp
        op_value = ListOp.IN if op_value in (ListOp.IN, StrCompOp.EQ) else ListOp.NIN
        comp = RefComparison
    else:
        op = StrCompOp
        comp = StrComparison
    return comp(field, op(op_value), value)


@typechecked
def _map_filter_exp(
    entity_name: str, filter_exp: FExpression, property_map: dict
) -> FExpression:
    if isinstance(
        filter_exp,
        (IntComparison, FloatComparison, StrComparison, ListComparison, RefComparison),
    ):
        # get the field
        field = filter_exp.field
        # add entity to field if it doesn't have one already
        if ":" not in field:
            field = f"{entity_name}:{field}"
        # map field to new syntax (e.g. STIX to OCSF)
        dmm = reverse_mapping(property_map)   #TEMP: do this once, right after loading
        map_result = translate_comparison_to_ocsf(dmm, field, filter_exp.op, filter_exp.value)
        # Build a MultiComp if field maps to several values
        if len(map_result) > 1:
            filter_exp = MultiComp(
                ExpOp.OR, [_create_comp(field, op, value) for field, op, value in map_result]
            )
        elif len(map_result) == 1:  # it maps to a single value
            mapping = map_result[0]
            filter_exp.field = mapping[0]
            filter_exp.op = mapping[1]
            filter_exp.value = mapping[2]
        else:  # pass-through
            pass
        # TODO: for RefComparison, map the attribute in value (may not be possible here)

    elif isinstance(filter_exp, BoolExp):
        # recursively map boolean expressions
        filter_exp = BoolExp(
            _map_filter_exp(entity_name, filter_exp.lhs, property_map),
            filter_exp.op,
            _map_filter_exp(entity_name, filter_exp.rhs, property_map),
        )
    elif isinstance(filter_exp, MultiComp):
        # normally, this should be unreachable
        # if this becomes a valid case, we need to change
        # the definition of MultiComp to accept a MultiComp
        # in addition to Comparisons in its `comps` list
        filter_exp = MultiComp(
            filter_exp.op,
            [_map_filter_exp(entity_name, x, property_map) for x in filter_exp.comps],
        )
    return filter_exp


@typechecked
def _add_reference_branches_for_filter(graph: IRGraph, filter_node: Filter):
    if filter_node not in graph:
        raise IRGraphMissingNode("Internal error: filter node expected")
    else:
        for refvalue in filter_node.get_references():
            r = graph.add_node(Reference(refvalue.reference))
            p = graph.add_node(ProjectAttrs([refvalue.attribute]), r)
            graph.add_edge(p, filter_node)


class _KestrelT(Transformer):
    def __init__(
        self,
        default_variable=DEFAULT_VARIABLE,
        default_sort_order=DEFAULT_SORT_ORDER,
        token_prefix="",
        entity_map={},
        property_map={},
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
        # TODO: move the var+var into expression in Lark
        variable_node = Variable(args[0].value)
        graph, root = args[1]
        graph.add_node(variable_node, root)
        return graph

    def expression(self, args):
        # TODO: add more clauses than WHERE and ATTR
        # TODO: think about order of clauses when turning into nodes
        graph = IRGraph()
        reference = graph.add_node(args[0])
        root = reference
        if len(args) > 1:
            for clause in args[1:]:
                graph.add_node(clause, root)
                root = clause
                if isinstance(clause, Filter):
                    # this is where_clause
                    _add_reference_branches_for_filter(graph, clause)
        return graph, root

    def vtrans(self, args):
        if len(args) == 1:
            return Reference(args[0].value)
        else:
            # TODO: transformer support
            ...

    def new(self, args):
        # TODO: use entity type

        graph = IRGraph()
        if len(args) == 1:
            # Try to get entity type from first entity
            data = args[0]
        else:
            data = args[1]
        data_node = Construct(data)
        graph.add_node(data_node)
        return graph, data_node

    def var_data(self, args):
        if isinstance(args[0], Token):
            # TODO
            ...
        else:
            v = args[0]
        return v

    def json_objs(self, args):
        return args

    def json_obj(self, args):
        return dict(args)

    def json_pair(self, args):
        v = args[0].value
        if "ESCAPED_STRING" in args[0].type:
            v = unescape_quoted_string(v)
        return v, args[1]

    def json_value(self, args):
        v = args[0].value
        if args[0].type == self.token_prefix + "ESCAPED_STRING":
            v = unescape_quoted_string(v)
        elif args[0].type == self.token_prefix + "NUMBER":
            v = float(v) if "." in v else int(v)
        return v

    def get(self, args):
        graph = IRGraph()
        entity_name = args[0].value
        mapped_entity_name = self.entity_map.get(entity_name, entity_name)

        # prepare Filter node
        filter_node = args[2]
        filter_node.exp = _map_filter_exp(
            args[0].value, filter_node.exp, self.property_map
        )

        # add basic Source and Filter nodes
        source_node = graph.add_node(args[1])
        filter_node = graph.add_node(filter_node, source_node)

        # add reference nodes if used in Filter
        _add_reference_branches_for_filter(graph, filter_node)

        projection_node = graph.add_node(ProjectEntity(mapped_entity_name), filter_node)
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

    def attr_clause(self, args):
        attrs = args[0].split(",")
        attrs = [attr.strip() for attr in attrs]
        return ProjectAttrs(attrs)

    def sort_clause(self, args):
        # args[0] is Token('BY', 'BY')
        return Sort(*args[1:])

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

    def reference_or_simple_string(self, args):
        vname = args[0].value
        attr = args[1].value if len(args) > 1 else None
        return ReferenceValue(vname, attr)

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
        return DataSource(args[0].value)

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

    def offset_clause(self, args):
        n = int(args[0])
        return Offset(n)

    def disp(self, args):
        graph, root = args[0]
        graph.add_node(Return(), root)
        return graph
