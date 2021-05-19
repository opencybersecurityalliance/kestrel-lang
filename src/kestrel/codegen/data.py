import json
import pathlib
import uuid

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
        dataframe = pd.DataFrame(data)
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


def dump_data_to_file(store, input_entity_table, file_path):
    p = pathlib.Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    input_data = store.lookup(input_entity_table) if input_entity_table else []
    dump_format = _get_dump_format(p)
    if dump_format == "csv":
        pd.DataFrame(input_data).to_csv(file_path)
    elif dump_format == "parquet":
        pd.DataFrame(input_data).to_parquet(file_path)
    elif dump_format == "json":
        data = pd.DataFrame(input_data).to_json(orient="records")
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
