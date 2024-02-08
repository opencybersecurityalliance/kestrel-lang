import logging
from datetime import datetime
from typing import Iterable, Mapping, Optional
from uuid import UUID

from opensearchpy import OpenSearch
from pandas import DataFrame, json_normalize

from kestrel.interface.datasource.base import AbstractDataSourceInterface
from kestrel.ir.graph import IRGraphEvaluable
from kestrel.ir.instructions import (
    DataSource,
    Instruction,
    Return,
    Variable,
    Filter,
    SourceInstruction,
    TransformingInstruction,
    SolePredecessorTransformingInstruction,
)

from kestrel_datasource_opensearch.config import load_config
from kestrel_datasource_opensearch.ossql import OpenSearchTranslator


_logger = logging.getLogger(__name__)


def _dt2ts(ts: datetime) -> str:
    """Convert a Python datetime to an ISO timestamp"""
    return f"{ts}Z"


def _os2df(result: dict) -> DataFrame:
    """Convert an OpenSearch SQL query result response to a DataFrame"""
    rows = [i["_source"] for i in result["hits"]["hits"]]
    return json_normalize(rows)


def read_sql(sql: str, conn: OpenSearch) -> DataFrame:
    """Execute `sql` and return the results as a DataFrame, a la pandas.read_sql"""
    query_resp = conn.http.post("/_plugins/_sql?format=json", body={"query": sql})
    return _os2df(query_resp)


class OpenSearchInterface(AbstractDataSourceInterface):
    def __init__(
        self,
        serialized_cache_catalog: Optional[str] = None,
        session_id: Optional[UUID] = None,
    ):
        super().__init__(serialized_cache_catalog, session_id)
        self.config = load_config()

    @property
    def name(self):
        return "opensearch"

    def store(
        self,
        instruction_id: UUID,
        data: DataFrame,
    ):
        raise NotImplementedError("OpenSearchInterface.store")  # TEMP

    def evaluate_graph(
        self,
        graph: IRGraphEvaluable,
        instructions_to_evaluate: Optional[Iterable[Instruction]] = None,
    ) -> Mapping[UUID, DataFrame]:
        mapping = {}
        if not instructions_to_evaluate:
            instructions_to_evaluate = graph.get_sink_nodes()
        for instruction in instructions_to_evaluate:
            translator = self._evaluate_instruction_in_graph(graph, instruction)
            # TODO: may catch error in case evaluation starts from incomplete SQL
            _logger.debug("SQL query generated: %s", translator.result())
            ds = self.config.indexes[translator.datasource]
            conn = self.config.connections[ds.connection]
            client = OpenSearch(
                [conn.url],
                http_auth=(conn.auth.username, conn.auth.password),
                verify_certs=conn.verify_certs,
            )
            mapping[instruction.id] = read_sql(translator.result(), client)
        return mapping

    def _evaluate_instruction_in_graph(
        self,
        graph: IRGraphEvaluable,
        instruction: Instruction,
    ) -> OpenSearchTranslator:
        _logger.debug("instruction: %s", str(instruction))
        translator = None
        if isinstance(instruction, TransformingInstruction):
            trunk, _r2n = graph.get_trunk_n_branches(instruction)
            translator = self._evaluate_instruction_in_graph(graph, trunk)

            if isinstance(instruction, SolePredecessorTransformingInstruction):
                if isinstance(instruction, Return):
                    pass
                elif isinstance(instruction, Variable):
                    pass
                else:
                    translator.add_instruction(instruction)

            elif isinstance(instruction, Filter):
                translator.add_instruction(instruction)

            else:
                raise NotImplementedError(f"Unknown instruction type: {instruction}")

        elif isinstance(instruction, SourceInstruction):
            if isinstance(instruction, DataSource):
                ds = self.config.indexes[instruction.datasource]
                translator = OpenSearchTranslator(
                    _dt2ts, ds.timestamp, instruction.datasource
                )
                translator.add_instruction(instruction)
            else:
                raise NotImplementedError(f"Unhandled instruction type: {instruction}")

        return translator
