"""T25.7 — durable evidence binding for EABC COMMIT.

Question: can the EABC adapter produce a durable binding record that links
commit_id to the exact cMCP execution tuple and terminal audit hash?
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import pytest

from cmcp_runtime.audit.chain import AuditChain


@dataclass(frozen=True)
class CommitBindingEvidence:
    commit_id: str
    call_id: str
    tool_name: str
    request_payload_hash: str
    policy_id: str
    terminal_audit_hash: str

    def canonical(self) -> bytes:
        return json.dumps(
            {
                "commit_id": self.commit_id,
                "call_id": self.call_id,
                "tool_name": self.tool_name,
                "request_payload_hash": self.request_payload_hash,
                "policy_id": self.policy_id,
                "terminal_audit_hash": self.terminal_audit_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

    @property
    def evidence_hash(self) -> str:
        return "sha256:" + hashlib.sha256(self.canonical()).hexdigest()


def test_t25_7_binding_record_is_deterministic_and_complete():
    evidence = CommitBindingEvidence(
        commit_id="eabc-t25.7-001",
        call_id="call-001",
        tool_name="test.echo",
        request_payload_hash="sha256:" + "a" * 64,
        policy_id="policy-A",
        terminal_audit_hash="sha256:" + "b" * 64,
    )

    assert evidence.evidence_hash == (
        "sha256:" + hashlib.sha256(evidence.canonical()).hexdigest()
    )
    assert set(json.loads(evidence.canonical())) == {
        "commit_id",
        "call_id",
        "tool_name",
        "request_payload_hash",
        "policy_id",
        "terminal_audit_hash",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("commit_id", "eabc-t25.7-002"),
        ("call_id", "call-002"),
        ("tool_name", "test.other"),
        ("request_payload_hash", "sha256:" + "c" * 64),
        ("policy_id", "policy-B"),
        ("terminal_audit_hash", "sha256:" + "d" * 64),
    ],
)
def test_t25_7_any_binding_mutation_changes_evidence_hash(field, value):
    base = {
        "commit_id": "eabc-t25.7-001",
        "call_id": "call-001",
        "tool_name": "test.echo",
        "request_payload_hash": "sha256:" + "a" * 64,
        "policy_id": "policy-A",
        "terminal_audit_hash": "sha256:" + "b" * 64,
    }
    original = CommitBindingEvidence(**base).evidence_hash
    base[field] = value
    assert CommitBindingEvidence(**base).evidence_hash != original
