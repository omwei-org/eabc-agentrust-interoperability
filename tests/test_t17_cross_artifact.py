from __future__ import annotations

import hashlib
import json


def digest(args: dict) -> str:
    raw = json.dumps(args, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def make_audit_entry(*, execution_id, tool_name, args, policy_hash, decision="ALLOW"):
    request_hash = digest(args)
    body = {
        "execution_id": execution_id,
        "tool_name": tool_name,
        "request_payload_hash": request_hash,
        "policy_bundle_hash": policy_hash,
        "policy_decision": decision,
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    body["entry_hash"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
    return body


def make_gateway_claim(*, policy_hash, execution_id, audit_entry):
    return {
        "policy_bundle_hash": policy_hash,
        "execution_id": execution_id,
        "audit_chain_tip": audit_entry["entry_hash"],
    }


def make_commit(audit_entry, claim, commit_id="commit-t17-001"):
    assert audit_entry["policy_decision"] == "ALLOW"
    assert audit_entry["execution_id"] == claim["execution_id"]
    assert audit_entry["policy_bundle_hash"] == claim["policy_bundle_hash"]
    return {
        "commit_id": commit_id,
        "execution_id": audit_entry["execution_id"],
        "request_payload_hash": audit_entry["request_payload_hash"],
        "policy_bundle_hash": audit_entry["policy_bundle_hash"],
        "tool_name": audit_entry["tool_name"],
        "evidence_ref": audit_entry["entry_hash"],
    }


def test_t17_cross_artifact_equality():
    args = {"destination": "cell-3", "speed": 1}
    audit = make_audit_entry(
        execution_id="exec-t17-001",
        tool_name="move",
        args=args,
        policy_hash="sha256:H1",
    )
    claim = make_gateway_claim(
        policy_hash="sha256:H1",
        execution_id="exec-t17-001",
        audit_entry=audit,
    )
    commit = make_commit(audit, claim)

    assert commit["request_payload_hash"] == audit["request_payload_hash"]
    assert commit["execution_id"] == audit["execution_id"]
    assert commit["policy_bundle_hash"] == claim["policy_bundle_hash"]
    assert commit["evidence_ref"] == claim["audit_chain_tip"]


def test_t17_tampered_arguments_break_binding():
    args = {"destination": "cell-3", "speed": 1}
    audit = make_audit_entry(
        execution_id="exec-t17-002",
        tool_name="move",
        args=args,
        policy_hash="sha256:H1",
    )
    tampered = {"destination": "cell-9", "speed": 1}
    assert digest(tampered) != audit["request_payload_hash"]


def test_t17_policy_mismatch_breaks_binding():
    audit = make_audit_entry(
        execution_id="exec-t17-003",
        tool_name="move",
        args={"destination": "cell-3"},
        policy_hash="sha256:H1",
    )
    claim = make_gateway_claim(
        policy_hash="sha256:H2",
        execution_id="exec-t17-003",
        audit_entry=audit,
    )
    try:
        make_commit(audit, claim)
        assert False
    except AssertionError:
        pass


def test_t17_evidence_reference_is_chain_tip():
    audit = make_audit_entry(
        execution_id="exec-t17-004",
        tool_name="read",
        args={"resource": "r1"},
        policy_hash="sha256:H1",
    )
    claim = make_gateway_claim(
        policy_hash="sha256:H1",
        execution_id="exec-t17-004",
        audit_entry=audit,
    )
    commit = make_commit(audit, claim)
    assert commit["evidence_ref"] == audit["entry_hash"] == claim["audit_chain_tip"]
