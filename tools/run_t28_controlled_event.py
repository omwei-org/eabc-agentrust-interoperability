"""Recompute and print the T28 controlled-event verification result."""

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


def main() -> None:
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    event, trace, eabc = d["event"], d["trace_evidence"], d["eabc_evidence"]

    action_ref = digest({
        "agent_id": event["agent_id"],
        "action_type": event["action_type"],
        "action_scope": event["action_scope"],
        "action_timestamp": event["action_timestamp"],
    })
    request_digest = digest({
        "tool_name": eabc["tool_name"],
        "arguments": {
            "event_id": event["event_id"],
            "action_ref": action_ref,
            "material_id": event["action"]["material_id"],
            "from": event["action"]["from"],
            "to": event["action"]["to"],
        },
    })
    result = {
        "event_id": event["event_id"],
        "trace_action_ref_match": action_ref == trace["action_ref"],
        "eabc_request_digest_match": request_digest == eabc["request_payload_hash"],
        "call_binding_match": trace["call_id"] == eabc["call_id"] == event["call_id"],
        "action_binding_match": trace["action_ref"] == eabc["action_ref"] == action_ref,
        "authority": eabc["authority"],
        "commit": eabc["commit"],
        "effect": eabc["effect"],
    }
    result["cross_source_binding"] = all([
        result["trace_action_ref_match"],
        result["eabc_request_digest_match"],
        result["call_binding_match"],
        result["action_binding_match"],
    ])
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
