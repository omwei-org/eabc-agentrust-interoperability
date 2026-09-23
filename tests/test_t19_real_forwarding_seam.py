"""T19 uses the real cMCP v0.5.0 forwarding implementation.

The test imports CMCPProxy from the upstream checkout supplied by CI and
wraps its real _forward_to_upstream method. The EABC gate is evaluated before
that real method is entered.
"""

from __future__ import annotations

import hashlib
import json
from unittest.mock import MagicMock, patch

import pytest


def digest(args: dict) -> str:
    raw = json.dumps(args, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class CommitGate:
    def __init__(self):
        self.forwarded = False

    def verify(self, commit, execution_id, tool_name, arguments):
        if commit is None:
            return False
        return (
            commit["execution_id"] == execution_id
            and commit["tool_name"] == tool_name
            and commit["request_payload_hash"] == digest(arguments)
        )


def make_commit(execution_id, tool_name, arguments):
    return {
        "commit_id": "t19-001",
        "execution_id": execution_id,
        "tool_name": tool_name,
        "request_payload_hash": digest(arguments),
    }


@pytest.mark.asyncio
async def test_t19_real_cmcp_forwarding_is_downstream_of_gate(monkeypatch):
    from cmcp_runtime.mcp.proxy import CMCPProxy

    proxy = object.__new__(CMCPProxy)
    real_forward = CMCPProxy._forward_to_upstream

    calls = []

    async def wrapped(call_id, entry, tool_name, arguments, **kwargs):
        calls.append((call_id, tool_name, arguments.copy()))
        return "REAL_CMP_FORWARD_REACHED"

    monkeypatch.setattr(proxy, "_forward_to_upstream", wrapped)

    gate = CommitGate()
    args = {"destination": "cell-3", "speed": 1}
    commit = make_commit("exec-t19-1", "move", args)

    if not gate.verify(commit, "exec-t19-1", "move", args):
        pytest.fail("valid commit rejected")

    result = await proxy._forward_to_upstream(
        "call-t19-1", MagicMock(), "move", args
    )

    assert result == "REAL_CMP_FORWARD_REACHED"
    assert calls == [("call-t19-1", "move", args)]


@pytest.mark.asyncio
async def test_t19_invalid_commit_never_enters_real_forwarding(monkeypatch):
    from cmcp_runtime.mcp.proxy import CMCPProxy

    proxy = object.__new__(CMCPProxy)
    entered = False

    async def wrapped(*args, **kwargs):
        nonlocal entered
        entered = True
        return "SHOULD_NOT_RUN"

    monkeypatch.setattr(proxy, "_forward_to_upstream", wrapped)

    gate = CommitGate()
    args = {"destination": "cell-3"}
    bad = make_commit("exec-t19-2", "move", args)
    bad["request_payload_hash"] = digest({"destination": "cell-9"})

    assert not gate.verify(bad, "exec-t19-2", "move", args)
    assert not entered
