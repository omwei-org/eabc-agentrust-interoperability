import json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TRACE_ID="iv002-shared-001"
EABC_ID="iv002-shared-001"
E1_HASH="683781cd9459dad646062f5e9975a233cad3308268ffa931dc558673cf894db9"
E2_HASH="5cdffc8d98df393fd007e7f82cfd3a07b56aa11eb22a0a52a9a2dcdda0c1771e"

def load(p): return json.loads((ROOT/p).read_text())

def test_e1_binding_is_independently_checkable():
    e=load("evidence/iv002-path2/iv002-shared-001-eabc-e1.json")
    assert e["command_id"] == EABC_ID
    assert e["shared_event_id"] == EABC_ID
    assert e["governed_action_digest"] == e["execution"]["payload_digest"]

def test_e2_preserves_identity_but_diverges_execution():
    e=load("evidence/iv002-path2/iv002-shared-001-eabc-e2.json")
    assert e["command_id"] == EABC_ID
    assert e["shared_event_id"] == EABC_ID
    assert e["governed_action_digest"] != e["execution"]["payload_digest"]
    assert e["execution"]["post_gate_transform"] is True

def test_e3_binding_is_unresolved():
    c=load("evidence/iv002-path2/cba-iv002-shared-001-e3.json")
    e=load("evidence/iv002-path2/iv002-shared-001-eabc-e1.json")
    assert c["expected_trace_call_id"] != e["command_id"]

def test_trace_hash_is_the_frozen_controlled_artifact():
    c=load("evidence/iv002-path2/cba-iv002-shared-001-e1.json")
    assert c["trace_artifact_hash"] == "sha256:fc511fffec6f61fc35153513c8d9fbbe3e5ebb8e46655094145f8388a4d208b5"
