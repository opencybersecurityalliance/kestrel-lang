import logging
from typing import Iterable, Mapping, Optional
from uuid import UUID

from opensearchpy import OpenSearch
from pandas import DataFrame, concat, json_normalize

from kestrel.exceptions import DataSourceError
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


def _jdbc2df(schema: dict, datarows: dict) -> DataFrame:
    """Convert a JDBC query result response to a DataFrame"""
    columns = [c.get("alias", c["name"]) for c in schema]
    return DataFrame(datarows, columns=columns)


def read_sql(sql: str, conn: OpenSearch) -> DataFrame:
    """Execute `sql` and return the results as a DataFrame, a la pandas.read_sql"""
    # https://opensearch.org/docs/latest/search-plugins/sql/sql-ppl-api/#query-api
    body = {
        "fetch_size": 10000,  # Should we make this configurable?
        "query": sql,
    }
    query_resp = conn.http.post("/_plugins/_sql?format=jdbc", body=body)
    status = query_resp.get("status", 500)
    if status != 200:
        raise DataSourceError(f"OpenSearch query returned {status}")
    _logger.debug(
        "total=%d size=%d rows=%d",
        query_resp["total"],
        query_resp["size"],
        len(query_resp["datarows"]),
    )

    # Only the first page contains the schema
    # https://opensearch.org/docs/latest/search-plugins/sql/sql-ppl-api/#paginating-results
    schema = query_resp["schema"]
    dfs = []
    done = False
    while not done:
        dfs.append(_jdbc2df(schema, query_resp["datarows"]))
        cursor = query_resp.get("cursor")
        if not cursor:
            break
        query_resp = conn.http.post(
            "/_plugins/_sql?format=jdbc", body={"cursor": cursor}
        )

    # Merge all pages together
    return concat(dfs)


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
            ds = self.config.indexes[translator.table]  # table == datasource
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
                    ds.timestamp_format,
                    ds.timestamp,
                    instruction.datasource,
                    ds.data_model_map,
                )
            else:
                raise NotImplementedError(f"Unhandled instruction type: {instruction}")

        return translator
