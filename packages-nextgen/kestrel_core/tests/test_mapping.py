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
    assert res == ["network_connection_info", "network_traffic"]


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
    assert res == "process"
    res = from_ocsf_names.get("network_connection_info")
    assert res == "network"
    res = from_ocsf_names.get("network_traffic")
    assert res == "network"
    res = from_ocsf_names.get("network_endpoint")
    assert res == ["client", "destination", "server", "source"]

    res = from_ocsf_attrs.get("process.name")
    assert res == "process.name"
    res = from_ocsf_attrs.get("process.cmd_line")
    assert res == "process.command_line"
    res = from_ocsf_attrs.get("process.file.hashes[?algorithm_id == 1].value")
    assert res == "process.hash.md5"
    res = from_ocsf_attrs.get("process.file.path")
    assert res == "process.executable"
    res = from_ocsf_attrs.get("process.parent_process.file.path")
    assert res == "process.parent.executable"
    res = from_ocsf_attrs.get("process.parent_process.tid")
    assert res == "process.parent.thread.id"
    res = from_ocsf_attrs.get("src_endpoint.domain")
    assert len(res) == 2 and "client.domain" in res and "source.domain" in res
    res = from_ocsf_attrs.get("src_endpoint.location.city")
    assert (len(res) == 2 and "client.geo.city_name" in res and
            "source.geo.city_name" in res)
    res = from_ocsf_attrs.get("tls.certificate.created_time")
    assert res == "file.x509.not_before"
    res = from_ocsf_attrs.get("tls.certificate.expiration_time")
    assert res == "file.x509.not_after"
    res = from_ocsf_attrs.get("tls.certificate.fingerprints.algorithm")
    assert res == "file.x509.signature_algorithm"
    res = from_ocsf_attrs.get("traffic.packets_in")
    assert (len(res) == 2 and "destination.packets" in res and
            "server.packets" in res)
    res = from_ocsf_attrs.get("file.hashes[?algorithm_id == 4].value")
    assert (len(res) == 2 and "hash.sha512" in res and "file.hash.sha512" in res)
