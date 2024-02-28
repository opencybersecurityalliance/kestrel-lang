from pandas import DataFrame
import tempfile
import base64
import sqlparse
from pygments import highlight
from pygments.lexers.sql import SqlLexer
from pygments.formatters import HtmlFormatter
import networkx as nx
import matplotlib.pyplot as plt

from kestrel.display import Display, GraphExplanation
from kestrel.ir.graph import IRGraph


def to_html_blocks(d: Display) -> str:
    if isinstance(d, DataFrame):
        yield d.to_html()
    elif isinstance(d, GraphExplanation):
        for graphlet in d.graphlets:
            graph = IRGraph(graphlet.graph)
            plt.figure(figsize=(4, 2))
            nx.draw(graph)
            with tempfile.NamedTemporaryFile(delete_on_close=False) as tf:
                tf.close()
                plt.savefig(tf.name, format="png")
                with open(tf.name, "rb") as tfx:
                    data = tfx.read()

            img = data_uri = base64.b64encode(data).decode("utf-8")
            imgx = f'<img src="data:image/png;base64,{img}">'
            yield imgx

            query_indented = sqlparse.format(
                graphlet.query, reindent=True, keyword_case="upper"
            )
            query = highlight(query_indented, SqlLexer(), HtmlFormatter())
            style = "<style>" + HtmlFormatter().get_style_defs() + "</style>"
            yield style + query
