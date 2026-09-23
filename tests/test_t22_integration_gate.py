from __future__ import annotations

import hashlib
import json


def digest(arguments):
    return "sha256:" + hashlib.sha256(
        json.dumps(arguments, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class RealPathHarness:
    def __init__(self):
        self.effects = []

    def call_tool(self, *, commit, call_id, tool_name, arguments):
        if commit is None:
            raise PermissionError("NO_COMMIT")
        if commit["call_id"] != call_id:
            raise PermissionError("CALL_ID_MISMATCH")
        if commit["tool_name"] != tool_name:
            raise PermissionError("TOOL_MISMATCH")
        if commit["request_payload_hash"] != digest(arguments):
            raise PermissionError("REQUEST_DIGEST_MISMATCH")
        self._forward_to_upstream(call_id, tool_name, arguments)

    def _forward_to_upstream(self, call_id, tool_name, arguments):
        self.effects.append(
            {"call_id": call_id, "tool_name": tool_name, "arguments": arguments.copy()}
        )


def commit(call_id, tool_name, arguments):
    return {
        "commit_id": "t22-001",
        "call_id": call_id,
        "tool_name": tool_name,
        "request_payload_hash": digest(arguments),
    }


def test_t22_valid_path_produces_effect():
    h = RealPathHarness()
    args = {"destination": "cell-3", "speed": 1}
    h.call_tool(
        commit=commit("call-22-001", "move", args),
        call_id="call-22-001",
        tool_name="move",
        arguments=args,
    )
    assert len(h.effects) == 1
    assert digest(h.effects[0]["arguments"]) == digest(args)


def test_t22_no_commit_produces_no_effect():
    h = RealPathHarness()
    try:
        h.call_tool(
            commit=None,
            call_id="call-22-002",
            tool_name="move",
            arguments={"destination": "cell-3"},
        )
        assert False
    except PermissionError as exc:
        assert str(exc) == "NO_COMMIT"
    assert h.effects == []


def test_t22_wrong_call_produces_no_effect():
    h = RealPathHarness()
    args = {"destination": "cell-3"}
    c = commit("call-22-003", "move", args)
    try:
        h.call_tool(
            commit=c,
            call_id="call-OTHER",
            tool_name="move",
            arguments=args,
        )
        assert False
    except PermissionError as exc:
        assert str(exc) == "CALL_ID_MISMATCH"
    assert h.effects == []


def test_t22_wrong_digest_produces_no_effect():
    h = RealPathHarness()
    args = {"destination": "cell-3"}
    c = commit("call-22-004", "move", args)
    try:
        h.call_tool(
            commit=c,
            call_id="call-22-004",
            tool_name="move",
            arguments={"destination": "cell-9"},
        )
        assert False
    except PermissionError as exc:
        assert str(exc) == "REQUEST_DIGEST_MISMATCH"
    assert h.effects == []
