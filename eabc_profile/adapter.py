"""Reusable MCP execution-boundary adapter.

The adapter is intentionally transport-agnostic. It binds a commit to the
exact MCP execution tuple and provides single-use enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


def request_digest(tool_name: str, arguments: dict[str, Any]) -> str:
    payload = json.dumps(
        {"tool_name": tool_name, "arguments": arguments},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def action_binding_digest(
    *,
    agent_identity: str,
    execution_id: str,
    tool_name: str,
    request_payload_hash: str,
    policy_id: str,
) -> str:
    """Canonical binding for the executable action.

    The binding deliberately includes cMCP's execution correlation identity
    without treating execution_id itself as EABC authority.
    """
    payload = {
        "agent_identity": agent_identity,
        "execution_id": execution_id,
        "tool_name": tool_name,
        "request_payload_hash": request_payload_hash,
        "policy_id": policy_id,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class EABCCommit:
    commit_id: str
    agent_identity: str
    execution_id: str
    call_id: str
    tool_name: str
    request_payload_hash: str
    policy_id: str
    action_binding: str
    authority_ref: str


class EABCMCPAdapter:
    """Bind and consume EABC commits for an MCP execution attempt."""

    def __init__(self) -> None:
        self._consumed: set[str] = set()

    def validate(
        self,
        commit: EABCCommit,
        *,
        agent_identity: str,
        execution_id: str,
        call_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        policy_id: str,
    ) -> None:
        if commit.commit_id in self._consumed:
            raise PermissionError("EABC_COMMIT_REPLAY")

        request_hash = request_digest(tool_name, arguments)
        binding = action_binding_digest(
            agent_identity=agent_identity,
            execution_id=execution_id,
            tool_name=tool_name,
            request_payload_hash=request_hash,
            policy_id=policy_id,
        )
        candidate = EABCCommit(
            commit_id=commit.commit_id,
            agent_identity=agent_identity,
            execution_id=execution_id,
            call_id=call_id,
            tool_name=tool_name,
            request_payload_hash=request_hash,
            policy_id=policy_id,
            action_binding=binding,
            authority_ref=commit.authority_ref,
        )
        if candidate != commit:
            raise PermissionError("EABC_COMMIT_SUBSTITUTION")

        self._consumed.add(commit.commit_id)
