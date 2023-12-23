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
    res = mapping_utils.normalize_entity("process", "ecs", "ocsf")
    assert res == "process"
    res = mapping_utils.normalize_entity("i_dont_exist", "ecs", "ocsf")
    assert res == "i_dont_exist"
    res = mapping_utils.normalize_entity("network", "ecs", "ocsf")
    assert res == "network_activity"


def test_mapping_entity_attributes():
    res = mapping_utils.normalize_property("process.parent.executable",
                                           "ecs", "ocsf")
    assert res == "process.parent_process.file.path"
    res = mapping_utils.normalize_property("process.hash.md5", "ecs", "ocsf")
    assert res == "process.file.hashes[?algorithm_id == 1].value"
    res = mapping_utils.normalize_property("process.group.id", "ecs", "ocsf")
    assert res == "process.group.uid"
    res = mapping_utils.normalize_property("processx.non.existent",
                                           "ecs", "ocsf")
    assert res == "processx.non.existent"
    res = mapping_utils.normalize_property("file.hash.md5", "ecs", "ocsf")
    assert res == "file.hashes[?algorithm_id == 1].value"


def test_from_ocsf_dicionaries():
    from_ocsf_names, from_ocsf_attrs = mapping_utils.generate_from_ocsf_dictionaries("ecs")
    res = from_ocsf_names.get("process")
    assert (len(res) == 1 and "process" in res)
    res = from_ocsf_names.get("network_endpoint")
    assert (len(res) == 4 and "client" in res and "destination" in res and
            "server" in res and "source" in res)
    res = from_ocsf_attrs.get("process.name")
    assert (len(res) == 1 and "process.name" in res)
    res = from_ocsf_attrs.get("process.cmd_line")
    assert (len(res) == 1 and "process.command_line" in res)
    res = from_ocsf_attrs.get("process.file.hashes[?algorithm_id == 1].value")
    assert (len(res) == 1 and "process.hash.md5" in res)
    res = from_ocsf_attrs.get("process.file.path")
    assert (len(res) == 1 and "process.executable" in res)
    res = from_ocsf_attrs.get("process.parent_process.file.path")
    assert (len(res) == 1 and "process.parent.executable" in res)
    res = from_ocsf_attrs.get("process.parent_process.tid")
    assert (len(res) == 1 and "process.parent.thread.id" in res)
    res = from_ocsf_attrs.get("src_endpoint.domain")
    assert (len(res) == 2 and "client.domain" in res and
            "source.domain" in res)
    res = from_ocsf_attrs.get("src_endpoint.location.city")
    assert (len(res) == 2 and "client.geo.city_name" in res and
            "source.geo.city_name" in res)
    res = from_ocsf_attrs.get("tls.certificate.created_time")
    assert (len(res) == 1 and "file.x509.not_before" in res)
    res = from_ocsf_attrs.get("tls.certificate.expiration_time")
    assert (len(res) == 1 and "file.x509.not_after" in res)
    res = from_ocsf_attrs.get("tls.certificate.fingerprints.algorithm")
    assert (len(res) == 1 and "file.x509.signature_algorithm" in res)
    res = from_ocsf_attrs.get("traffic.packets_in")
    assert (len(res) == 2 and "destination.packets" in res and
            "server.packets" in res)
    res = from_ocsf_attrs.get("file.hashes[?algorithm_id == 4].value")
    assert (len(res) == 2 and "hash.sha512" in res and
            "file.hash.sha512" in res)
