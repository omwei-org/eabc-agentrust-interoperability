import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACE_ID = "iv002-shared-001"
EABC_ID = "iv002-shared-001"
E1_HASH = "4bef46a068ba51e47dade484f6c788883309a3b615082983f550492dc2d3dae0"
E2_HASH = "2fc95e0cc4843014d0ad61439a8a0ec1fac95714ca622a79326da6b032aabc7d"


def load(p):
    return json.loads((ROOT / p).read_text())


def content_sha256(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def test_e1_binding_is_independently_checkable():
    e = load("evidence/iv002-path2/iv002-shared-001-eabc-e1.json")
    assert e["command_id"] == EABC_ID
    assert e["shared_event_id"] == EABC_ID
    assert e["governed_action_digest"] == e["execution"]["payload_digest"]
    assert content_sha256("evidence/iv002-path2/iv002-shared-001-eabc-e1.json") == E1_HASH


def test_e2_preserves_identity_but_diverges_execution():
    e = load("evidence/iv002-path2/iv002-shared-001-eabc-e2.json")
    assert e["command_id"] == EABC_ID
    assert e["shared_event_id"] == EABC_ID
    assert e["governed_action_digest"] != e["execution"]["payload_digest"]
    assert e["execution"]["post_gate_transform"] is True
    assert content_sha256("evidence/iv002-path2/iv002-shared-001-eabc-e2.json") == E2_HASH


def test_e3_binding_is_unresolved():
    c = load("evidence/iv002-path2/cba-iv002-shared-001-e3.json")
    e = load("evidence/iv002-path2/iv002-shared-001-eabc-e1.json")
    assert c["expected_trace_call_id"] != e["command_id"]
    assert c["eabc_artifact_hash"] == f"sha256:{E1_HASH}"


def test_e1_cba_binds_to_the_actual_eabc_artifact():
    c = load("evidence/iv002-path2/cba-iv002-shared-001-e1.json")
    assert c["shared_event_id"] == EABC_ID
    assert c["eabc_artifact_hash"] == f"sha256:{E1_HASH}"
