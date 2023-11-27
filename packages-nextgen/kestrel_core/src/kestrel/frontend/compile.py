# Lark Transformer

from lark import Transformer
from typeguard import typechecked

from kestrel.ir.filter import (
    IntComparison,
    FloatComparison,
    StrComparison,
    ListComparison,
    ListOp,
    NumCompOp,
    StrCompOp,
    ExpOp,
    BoolExp,
)
from kestrel.ir.graph import IRGraph
from kestrel.ir.instructions import (
    Filter,
    ProjectEntity,
    Source,
    Variable,
    source_from_uri,
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


def _create_multiple_or_expression(field_list, op, value):
    res = None
    for field in field_list:
        comp = _create_comp(field, op, value)
        if res is None:
            res = comp
        else:
            res = BoolExp(res, ExpOp.OR, comp)
    return res


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
        return args[0]

    def statement(self, args):
        return args[0]

    def assignment(self, args):
        variable = Variable(args[0].value)
        return_type, source, filt = args[1]
        result = IRGraph()
        result.add_node(filt)
        result.add_source(source, filt)
        result.add_variable(variable, source)
        return result

    def get(self, args):
        # TODO: map entity for args[0].value
        entity_name = self.entity_map.get(args[0].value, args[0].value)
        args[0] = ProjectEntity(entity_name)
        return args

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
        # TODO: frontend field mapping
        mapped_field = self.property_map.get(field, field)
        op = args[1]
        value = args[2]
        if isinstance(mapped_field, (list, tuple)):
            comp = _create_multiple_or_expression(mapped_field, op, value)
        else:
            comp = _create_comp(mapped_field, op, value)
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
        return source_from_uri(args[0].value)
