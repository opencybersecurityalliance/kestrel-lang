import kestrel.mapping.utils as mapping_utils


def test_mapping_load_config():
    mapping_utils.load_standard_config("kestrel.mapping")
    entity_name_map = mapping_utils._entityname_mapping
    assert "stix" in entity_name_map
    assert "ocsf" in entity_name_map.get("stix", {})
    assert "ecs" in entity_name_map
    assert "ocsf" in entity_name_map.get("ecs", {})
    entity_attr_map = mapping_utils._entityattr_mapping
    assert "stix" in entity_attr_map
    assert "ocsf" in entity_attr_map.get("stix", {})
    assert "ecs" in entity_attr_map
    assert "ocsf" in entity_attr_map.get("ecs", {})


def test_mapping_entity_names():
    res = mapping_utils.translate_entityname("process", "ecs", "ocsf")
    assert res == "process"
    res = mapping_utils.translate_entityname("i_dont_exist", "ecs", "ocsf")
    assert res == "i_dont_exist"
    res = mapping_utils.translate_entityname("network", "ecs", "ocsf")
    assert res == ["network_connection_info", "network_traffic"]


def test_mapping_entity_attributes():
    res = mapping_utils.translate_entityattr("process.parent.executable", "ecs", "ocsf")
    assert res == "process.parent_process.file.path"
    res = mapping_utils.translate_entityattr("process.hash.md5", "ecs", "ocsf")
    assert res == "process.file.hashes[?algorithm_id == 1].value"
