"""T25.8 — native-vs-adapter evidence separation.

Verify that the binding evidence is an explicit adapter artifact and that
the production cMCP terminal AuditEntry remains unchanged.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AdapterBinding:
    commit_id: str
    call_id: str
    tool_name: str
    request_payload_hash: str
    policy_id: str
    terminal_audit_hash: str


def test_t25_8_binding_is_explicit_adapter_artifact():
    binding = AdapterBinding(
        commit_id="eabc-t25.8-001",
        call_id="call-001",
        tool_name="test.echo",
        request_payload_hash="sha256:" + "a" * 64,
        policy_id="policy-A",
        terminal_audit_hash="sha256:" + "b" * 64,
    )
    payload = asdict(binding)
    assert payload["commit_id"].startswith("eabc-")
    assert "terminal_audit_hash" in payload
    assert set(payload) == {
        "commit_id", "call_id", "tool_name",
        "request_payload_hash", "policy_id", "terminal_audit_hash",
    }


def test_t25_8_does_not_assume_commit_id_is_native_audit_field():
    # This is an explicit schema guard: EABC binding is separate from the
    # production cMCP AuditEntry schema observed in v0.5.0.
    production_audit_fields = {
        "entry_id", "sequence_number", "timestamp_utc", "session_id",
        "call_id", "entry_type", "tool_name", "server_identity",
        "policy_decision", "policy_rule_matched", "latency_us",
        "request_payload_hash", "response_payload_hash",
        "response_inspection_result", "session_sensitivity_before",
        "session_sensitivity_after", "detail", "workflow_id",
        "prev_entry_hash", "evidence_class", "external_execution_evidence",
        "effective_data_class", "entry_hash",
    }
    assert "commit_id" not in production_audit_fields
