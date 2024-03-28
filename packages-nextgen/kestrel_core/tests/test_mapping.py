import kestrel.mapping.utils as mapping_utils


def test_mapping_load_config():
    mapping_utils.load_standard_config("kestrel.mapping")
    entity_name_map = mapping_utils._entityname_mapping
    assert "stix" in entity_name_map
    assert "ocsf" in entity_name_map.get("stix", {})
    assert "ecs" in entity_name_map
    assert "ocsf" in entity_name_map.get("ecs", {})


def test_mapping_entity_names():
    res = mapping_utils.normalize_entity("process", "ecs", "ocsf")
    assert res == "process"
    res = mapping_utils.normalize_entity("i_dont_exist", "ecs", "ocsf")
    assert res == "i_dont_exist"
    res = mapping_utils.normalize_entity("network", "ecs", "ocsf")
    assert res == "network_activity"
