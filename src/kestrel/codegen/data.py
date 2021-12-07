import json
import pathlib
import uuid

from firepit.props import get_last, ref_type
from firepit.query import CoalescedColumn, Column, Join, Projection, Query
import pandas as pd

from kestrel.exceptions import MissingEntityType, NonUniformEntityType


def load_data(
    store, output_entity_table, input_data, input_entity_type=None, query_id=None
):
    # if input data is list of strings, load directly
    # logic handled in store
    if type(input_data) == str:
        data = json.loads(input_data)
    else:
        data = input_data
    if type(data) == list and type(data[0]) == str:
        if not input_entity_type:
            raise MissingEntityType
        data = data
        entity_type = input_entity_type
    else:
        # load any table-like input data with header information
        dataframe = pd.DataFrame(data).replace({pd.NA: None})
        entity_type = _extract_uniform_type(dataframe, input_entity_type)
        data = dataframe.to_dict(orient="records")

    store.load(output_entity_table, data, entity_type, query_id)
    return entity_type


def load_data_file(store, output_entity_table, file_path, input_entity_type=None):
    dump_format = _get_dump_format(file_path)
    if dump_format == "csv":
        data = pd.read_csv(file_path)
    elif dump_format == "parquet":
        data = pd.read_parquet(file_path)
    elif dump_format == "json":
        with open(file_path) as input_file:
            data = json.load(input_file)
    query_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(file_path)))
    entity_type = load_data(
        store, output_entity_table, data, input_entity_type, query_id
    )
    return entity_type


def _make_join(store, lhs, ref, rhs, proj):
    # Use the `ref` prop as the alias for table `rhs`
    # Important because e.g. network-traffic needs to JOIN ipv4-addr twice
    proj.extend(
        [
            Column(c, ref, f"{ref}.{c}")
            for c in store.columns(rhs)
            if c != "id" and c != ref
        ]
    )
    return Join(rhs, ref, "=", "id", how="LEFT OUTER", alias=ref, lhs=lhs)


def _auto_deref(store, input_entity_table, etype):
    # Automatically resolve all refs for backward compatibility
    all_types = set(store.types())
    props = store.columns(input_entity_table)
    proj = []
    qry = Query(input_entity_table)
    for prop in props:
        if prop.endswith("_ref"):
            rtypes = set(ref_type(etype, get_last(prop))) & all_types
            prev_table = input_entity_table
            if len(rtypes) > 1:
                assert set(rtypes) == {"ipv4-addr", "ipv6-addr"}
                # Special case for when we have BOTH IPv4 and IPv6
                for n in (4, 6):
                    qry.append(
                        Join(
                            f"ipv{n}-addr",
                            prop,
                            "=",
                            "id",
                            how="LEFT OUTER",
                            alias=f"{prop}{n}",
                            lhs=prev_table,
                        )
                    )
                v4_cols = set(store.columns("ipv4-addr"))
                v6_cols = set(store.columns("ipv6-addr"))
                # Coalesce columns that are common to both
                for c in v4_cols & v6_cols:
                    if c not in {"id", prop}:
                        names = [f"{prop}{n}.{c}" for n in (4, 6)]
                        proj.append(CoalescedColumn(names, f"{prop}.{c}"))
                # Collect columns that are exclusive to one table or the other
                for c in v4_cols - v6_cols:
                    if c not in {"id", prop}:
                        for a in ("src4", "dst4"):
                            proj.append(Column(c, a, f"{prop}.{c}"))
                for c in v6_cols - v4_cols:
                    if c not in {"id", prop}:
                        for a in ("src6", "dst6"):
                            proj.append(Column(c, a, f"{prop}.{c}"))
            else:
                rtype = list(rtypes)[0]
                if rtype in all_types:
                    # Need to join this table
                    qry.append(_make_join(store, prev_table, prop, rtype, proj))
                    prev_table = rtype
        else:
            proj.append(Column(prop, input_entity_table))
    qry.append(Projection(proj))
    return store.run_query(qry).fetchall()


def dump_data_to_file(store, input_entity_table, file_path):
    p = pathlib.Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    etype = store.table_type(input_entity_table)
    input_data = (
        _auto_deref(store, input_entity_table, etype) if input_entity_table else []
    )
    df = pd.DataFrame(input_data)
    df["type"] = etype
    dump_format = _get_dump_format(p)
    if dump_format == "csv":
        df.to_csv(file_path)
    elif dump_format == "parquet":
        df.to_parquet(file_path)
    elif dump_format == "json":
        data = df.to_json(orient="records")
        with open(file_path, "w") as output_file:
            output_file.write(data)


def _extract_uniform_type(dataframe, input_entity_type):
    # check if the input dataframe has "type" attribute and type is uniform
    # if passed, return entity type
    # if dataframe does not have "type", and input_entity_type is not None
    # use that, otherwise, raise Exception
    if "type" in dataframe:
        all_input_entity_types = dataframe["type"].unique()
        if len(all_input_entity_types) > 1:
            raise NonUniformEntityType(all_input_entity_types)
        else:
            return all_input_entity_types[0]
    elif input_entity_type:
        dataframe.loc[:, "type"] = input_entity_type
        return input_entity_type
    else:
        raise MissingEntityType


def _get_dump_format(path):
    # input: path is a path string or a Path from pathlib
    if isinstance(path, str):
        path = pathlib.Path(path)
    suffixes = path.suffixes
    if suffixes[-1] in [".gz", ".bz2", ".zip", ".xz"]:
        # supported compression suffix in pandas
        suffix = suffixes[-2]
    else:
        suffix = suffixes[-1]
    suffix = suffix[1:]
    if suffix in ["csv", "parquet", "json"]:
        return suffix
    else:
        raise NotImplementedError("unknown file dump format")
