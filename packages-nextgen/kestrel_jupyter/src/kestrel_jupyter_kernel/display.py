from pandas import DataFrame
import tempfile
import base64
import sqlparse
from typing import Iterable, Mapping
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.lexers.sql import SqlLexer
from pygments.lexers.kusto import KustoLexer
from pygments.formatters import HtmlFormatter
import networkx as nx
import matplotlib.pyplot as plt

from kestrel.display import Display, GraphExplanation
from kestrel.ir.graph import IRGraph
from kestrel.ir.instructions import Instruction, DataSource, Variable, Construct


def gen_label_mapping(g: IRGraph) -> Mapping[Instruction, str]:
    d = {}
    for n in g:
        if isinstance(n, Variable):
            d[n] = n.name
        elif isinstance(n, Construct):
            d[n] = n.id.hex[:4]
        elif isinstance(n, DataSource):
            d[n] = n.datasource
        else:
            d[n] = f"[{n.instruction.upper()}]"
    return d


def to_html_blocks(d: Display) -> Iterable[str]:
    if isinstance(d, DataFrame):
        yield d.to_html()
    elif isinstance(d, GraphExplanation):
        for graphlet in d.graphlets:
            graph = IRGraph(graphlet.graph)
            plt.figure(figsize=(4, 2))
            nx.draw(
                graph,
                with_labels=True,
                labels=gen_label_mapping(graph),
                font_size=8,
                node_size=260,
                node_color="#bfdff5",
            )
            with tempfile.NamedTemporaryFile(delete_on_close=False) as tf:
                tf.close()
                plt.savefig(tf.name, format="png")
                with open(tf.name, "rb") as tfx:
                    data = tfx.read()

            img = data_uri = base64.b64encode(data).decode("utf-8")
            imgx = f'<img src="data:image/png;base64,{img}">'
            yield imgx

            query = graphlet.query.statement
            if graphlet.query.language == "SQL":
                lexer = SqlLexer()
                query = sqlparse.format(query, reindent=True, keyword_case="upper")
            elif graphlet.query.language == "KQL":
                lexer = KustoLexer()
            else:
                lexer = guess_lexer(query)
            query = highlight(query, lexer, HtmlFormatter())
            style = "<style>" + HtmlFormatter().get_style_defs() + "</style>"
            yield style + query
