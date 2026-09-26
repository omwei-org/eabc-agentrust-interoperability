"""T28 — independent verification of the controlled TRACE × EABC event."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evidence/t28-controlled-event.json"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def test_t28_shared_event_binding():
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    event, trace, eabc, binding = d["event"], d["trace_evidence"], d["eabc_evidence"], d["binding"]

    action_ref = digest({
        "agent_id": event["agent_id"],
        "action_type": event["action_type"],
        "action_scope": event["action_scope"],
        "action_timestamp": event["action_timestamp"],
    })
    assert action_ref == trace["action_ref"] == eabc["action_ref"]

    request = {
        "tool_name": eabc["tool_name"],
        "arguments": {
            "event_id": event["event_id"],
            "action_ref": action_ref,
            "material_id": event["action"]["material_id"],
            "from": event["action"]["from"],
            "to": event["action"]["to"],
        },
    }
    assert digest(request) == eabc["request_payload_hash"]
    assert trace["event_id"] == eabc["event_id"] == binding["event_id"]
    assert trace["call_id"] == eabc["call_id"] == event["call_id"]
    assert binding["trace_action_ref"] == action_ref
    assert binding["eabc_commit_id"] == eabc["commit_id"]
    assert binding["eabc_request_payload_hash"] == eabc["request_payload_hash"]
    assert binding["binding"] == "MATCH"
    assert eabc["authority"] == "ALLOW"
    assert eabc["commit"] == "OBSERVED"
    assert eabc["effect"] == "APPLIED"


def test_t28_trace_evidence_digest_and_binding_digest():
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert digest(d["trace_evidence"]) == d["binding"]["trace_evidence_hash"]
    assert digest(d["binding"]) == d["binding_hash"]


def test_t28_action_substitution_breaks_binding():
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    event = d["event"]
    substituted = {
        "agent_id": event["agent_id"],
        "action_type": event["action_type"],
        "action_scope": "cell-a.material.delete",
        "action_timestamp": event["action_timestamp"],
    }
    assert digest(substituted) != d["trace_evidence"]["action_ref"]
