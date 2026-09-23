"""T18 source-seam tests.

These tests deliberately model the seam exposed by cMCP's _call_tool_impl:
Cedar/gateway admission -> _forward_to_upstream(call_id, entry, tool_name, arguments).

They do not modify the upstream cMCP runtime.
"""

from __future__ import annotations

import hashlib
import json


def digest(arguments: dict) -> str:
    raw = json.dumps(arguments, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class EABCForwardingGate:
    def __init__(self):
        self.forwarded = []

    def forward(self, *, commit: dict | None, execution_id: str, tool_name: str, arguments: dict):
        if commit is None:
            raise PermissionError("NO_COMMIT")
        if commit["execution_id"] != execution_id:
            raise PermissionError("EXECUTION_ID_MISMATCH")
        if commit["tool_name"] != tool_name:
            raise PermissionError("TOOL_MISMATCH")
        if commit["request_payload_hash"] != digest(arguments):
            raise PermissionError("REQUEST_DIGEST_MISMATCH")
        self.forwarded.append(arguments.copy())


def commit(execution_id: str, tool_name: str, arguments: dict, policy_hash="sha256:H1"):
    return {
        "commit_id": "t18-001",
        "execution_id": execution_id,
        "tool_name": tool_name,
        "request_payload_hash": digest(arguments),
        "policy_bundle_hash": policy_hash,
    }


def test_t18_valid_commit_allows_forward():
    gate = EABCForwardingGate()
    args = {"destination": "cell-3", "speed": 1}
    gate.forward(
        commit=commit("exec-18-1", "move", args),
        execution_id="exec-18-1",
        tool_name="move",
        arguments=args,
    )
    assert gate.forwarded == [args]


def test_t18_no_commit_blocks_forward():
    gate = EABCForwardingGate()
    try:
        gate.forward(
            commit=None,
            execution_id="exec-18-2",
            tool_name="move",
            arguments={"destination": "cell-3"},
        )
        assert False
    except PermissionError as exc:
        assert str(exc) == "NO_COMMIT"
    assert gate.forwarded == []


def test_t18_wrong_digest_blocks_forward():
    gate = EABCForwardingGate()
    prepared = {"destination": "cell-3"}
    c = commit("exec-18-3", "move", prepared)
    try:
        gate.forward(
            commit=c,
            execution_id="exec-18-3",
            tool_name="move",
            arguments={"destination": "cell-9"},
        )
        assert False
    except PermissionError as exc:
        assert str(exc) == "REQUEST_DIGEST_MISMATCH"
    assert gate.forwarded == []


def test_t18_wrong_execution_id_blocks_forward():
    gate = EABCForwardingGate()
    args = {"destination": "cell-3"}
    c = commit("exec-18-4", "move", args)
    try:
        gate.forward(
            commit=c,
            execution_id="exec-OTHER",
            tool_name="move",
            arguments=args,
        )
        assert False
    except PermissionError as exc:
        assert str(exc) == "EXECUTION_ID_MISMATCH"
    assert gate.forwarded == []


def test_t18_exact_arguments_reach_forwarding_seam():
    gate = EABCForwardingGate()
    args = {"destination": "cell-3", "speed": 1}
    c = commit("exec-18-5", "move", args)
    gate.forward(
        commit=c,
        execution_id="exec-18-5",
        tool_name="move",
        arguments=args,
    )
    assert digest(gate.forwarded[0]) == c["request_payload_hash"]
