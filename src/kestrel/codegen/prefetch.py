import logging
from copy import deepcopy
from kestrel.symboltable.symtable import SymbolTable
from kestrel.syntax.parser import parse_ecgpattern
from kestrel.utils import lowered_str_list
from kestrel.semantics.reference import make_deref_func, make_var_timerange_func
from kestrel.syntax.utils import (
    timedelta_seconds,
)
from kestrel.codegen.relations import (
    get_entity_id_attribute,
    fine_grained_relational_process_filtering,
    compile_identical_entity_search_pattern,
    build_pattern_from_ids,
)


_logger = logging.getLogger(__name__)


def do_prefetch(
    local_stage_varname,
    local_stage_varstruct,
    session,
    stmt,
    extra_prefetch_enabled_flag=True,
):
    """prefetch identical entities and associated entities.

    Put the input entities in the center of an observation and query the remote
    data source of associated with input variable, so we get back:

    1. all records about the input entities.

    2. associated entities such as parent/child processes of processes, processes of network-traffic, etc.

    Args:
        local_stage_varname (str): local variable name before prefetch
        local_stage_varstruct (str): local variable (VarStruct) before prefetch
    Returns:
        str: the entity table for the statement output variable
    """

    # STIX pattern for prefetch
    stix_pattern = None

    prefetch_ret_entity_table = stmt["output"] + "_prefetch"
    prefetch_fil_entity_table = prefetch_ret_entity_table + "_filtered"
    return_var_entity_table = stmt["output"]

    if (
        _is_prefetch_allowed_in_config(
            session.config["prefetch"], stmt["command"], stmt["type"]
        )
        and len(local_stage_varstruct)
        and local_stage_varstruct.data_source
        and extra_prefetch_enabled_flag
    ):
        _logger.info(f"generate pattern for prefetch {local_stage_varname}.")

        pattern_raw = compile_identical_entity_search_pattern(
            local_stage_varname,
            local_stage_varstruct,
            session.config["stixquery"]["support_id"],
        )

        if pattern_raw:
            _symtable = SymbolTable({local_stage_varname: local_stage_varstruct})
            pattern_ast = parse_ecgpattern(pattern_raw)
            deref_func = make_deref_func(session.store, _symtable)
            get_timerange_func = make_var_timerange_func(session.store, _symtable)
            pattern_ast.deref(deref_func, get_timerange_func)
            pattern_ast.add_center_entity(local_stage_varstruct.type)
            time_adj = tuple(
                map(
                    timedelta_seconds,
                    (
                        session.config["stixquery"]["timerange_start_offset"],
                        session.config["stixquery"]["timerange_stop_offset"],
                    ),
                )
            )
            ext_graph_pattern = deepcopy(stmt.get("where"))
            # TODO: check prune() logic, remove the "if" and just run content
            if ext_graph_pattern and stmt["command"].lower() == "get":
                ext_graph_pattern.prune_away_centered_graph(stmt["type"])
            _logger.debug(f"ext pattern in prefetch: {ext_graph_pattern}")
            _logger.debug(f"prefetch pattern before extend: {pattern_ast}")
            pattern_ast.extend("AND", ext_graph_pattern)
            _logger.debug(f"prefetch pattern after extend: {pattern_ast}")
            stix_pattern = pattern_ast.to_stix(stmt["timerange"], time_adj)
            _logger.info(f"STIX pattern generated in prefetch: {stix_pattern}")

    if stix_pattern:
        resp = session.data_source_manager.query(
            local_stage_varstruct.data_source,
            stix_pattern,
            session.session_id,
            session.store,
            stmt.get("limit"),
        )
        query_id = resp.load_to_store(session.store)

        # build the view in store
        session.store.extract(
            prefetch_ret_entity_table, stmt["type"], query_id, stix_pattern
        )

        prefetch_final_entity_table = _filter_prefetched_process(
            prefetch_fil_entity_table,
            session,
            local_stage_varstruct,
            prefetch_ret_entity_table,
            stmt["type"],
        )

        session.store.rename_view(prefetch_final_entity_table, return_var_entity_table)

        for v in [
            local_stage_varstruct.entity_table,
            prefetch_ret_entity_table,
            prefetch_fil_entity_table,
        ]:
            if not session.debug_mode:
                session.store.remove_view(v)

    else:
        _logger.info(f"prefetch does not happen without STIX pattern generated.")
        session.store.rename_view(
            local_stage_varstruct.entity_table, return_var_entity_table
        )

    return return_var_entity_table


def _filter_prefetched_process(
    prefetch_filtered_var_name,
    session,
    local_varstruct,
    prefetch_raw_entity_table,
    return_type,
):
    # default return
    ret_table = prefetch_raw_entity_table

    # special handling for process to filter out impossible relational processes
    # this is needed since STIX 2.0 does not have mandatory fields for
    # process and field like `pid` is not unique
    if return_type == "process" and get_entity_id_attribute(local_varstruct) not in (
        "id",
        "x_unique_id",
    ):
        _logger.debug(
            f"filter prefetched {return_type} for {prefetch_raw_entity_table}."
        )

        entity_ids = fine_grained_relational_process_filtering(
            local_varstruct,
            prefetch_raw_entity_table,
            session.store,
            session.config["prefetch"]["process_identification"],
        )

        if entity_ids:
            id_pattern = build_pattern_from_ids(return_type, entity_ids)
            session.store.extract(
                prefetch_filtered_var_name, return_type, None, id_pattern
            )
            _logger.debug("filter after prefetch succeeds.")
            ret_table = prefetch_filtered_var_name
        else:
            _logger.info(
                "no prefetched process found after filtering, return raw prefetch."
            )

    return ret_table


def _is_prefetch_allowed_in_config(prefetch_config, command_name, entity_type):
    if prefetch_config["switch_per_command"][
        command_name
    ] and entity_type not in lowered_str_list(prefetch_config["excluded_entities"]):
        return True
    else:
        return False
