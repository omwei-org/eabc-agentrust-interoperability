from __future__ import annotations

import hashlib
import json


def digest(args):
    raw = json.dumps(args, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def make_audit(call_id, tool_name, args, policy_hash="sha256:H1"):
    body = {
        "call_id": call_id,
        "tool_name": tool_name,
        "request_payload_hash": digest(args),
        "policy_bundle_hash": policy_hash,
        "policy_decision": "allow",
    }
    body["entry_hash"] = "sha256:" + hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return body


def make_commit(call_id, tool_name, args, policy_hash="sha256:H1"):
    return {
        "commit_id": "commit-t21-001",
        "call_id": call_id,
        "tool_name": tool_name,
        "request_payload_hash": digest(args),
        "policy_bundle_hash": policy_hash,
    }


def bind(commit, audit):
    if commit["call_id"] != audit["call_id"]:
        raise PermissionError("CALL_ID_MISMATCH")
    if commit["tool_name"] != audit["tool_name"]:
        raise PermissionError("TOOL_MISMATCH")
    if commit["request_payload_hash"] != audit["request_payload_hash"]:
        raise PermissionError("REQUEST_DIGEST_MISMATCH")
    if commit["policy_bundle_hash"] != audit["policy_bundle_hash"]:
        raise PermissionError("POLICY_MISMATCH")
    return {"commit_id": commit["commit_id"], "evidence_ref": audit["entry_hash"]}


def test_t21_valid_commit_binds_to_call_and_evidence():
    args = {"destination": "cell-3"}
    audit = make_audit("call-21-001", "move", args)
    commit = make_commit("call-21-001", "move", args)
    link = bind(commit, audit)
    assert link["commit_id"] == "commit-t21-001"
    assert link["evidence_ref"] == audit["entry_hash"]


def test_t21_wrong_call_id_rejected():
    args = {"destination": "cell-3"}
    audit = make_audit("call-21-002", "move", args)
    commit = make_commit("call-OTHER", "move", args)
    try:
        bind(commit, audit)
        assert False
    except PermissionError as exc:
        assert str(exc) == "CALL_ID_MISMATCH"


def test_t21_wrong_digest_rejected():
    args = {"destination": "cell-3"}
    audit = make_audit("call-21-003", "move", args)
    commit = make_commit("call-21-003", "move", {"destination": "cell-9"})
    try:
        bind(commit, audit)
        assert False
    except PermissionError as exc:
        assert str(exc) == "REQUEST_DIGEST_MISMATCH"


def test_t21_wrong_policy_rejected():
    args = {"destination": "cell-3"}
    audit = make_audit("call-21-004", "move", args, "sha256:H1")
    commit = make_commit("call-21-004", "move", args, "sha256:H2")
    try:
        bind(commit, audit)
        assert False
    except PermissionError as exc:
        assert str(exc) == "POLICY_MISMATCH"


def test_t21_wrong_tool_rejected():
    args = {"destination": "cell-3"}
    audit = make_audit("call-21-005", "move", args)
    commit = make_commit("call-21-005", "delete", args)
    try:
        bind(commit, audit)
        assert False
    except PermissionError as exc:
        assert str(exc) == "TOOL_MISMATCH"
