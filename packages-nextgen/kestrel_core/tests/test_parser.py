from kestrel.frontend.parser import parse_kestrel
from kestrel.ir.instructions import Filter

import pytest


@pytest.mark.parametrize(
    "stmt", [
        "x = GET thing FROM ds WHERE foo = 'bar'",
        "x = GET thing FROM ds WHERE foo > 1.5",
        r"x = GET thing FROM ds WHERE foo = r'C:\TMP'",
        "x = GET thing FROM ds WHERE foo = 'bar' OR baz != 42",
        "x = GET thing FROM ds WHERE foo = 'bar' AND baz IN (1, 2, 3)",
        "x = GET thing FROM ds WHERE foo = 'bar' AND baz IN (1)",
    ]
)
def test_parser_get_statements(stmt):
    """
    This test isn't meant to be comprehensive, but checks basic transformer functionality.

    This will need to be updated as we build out the new Transformer
    """

    result = parse_kestrel(stmt)
    #TODO: assert isinstance(result, IRGraph)?

    # Ensure result is serializable
    #TODO: _ = result.to_json()
