"""Reusable MCP execution-boundary adapter.

The adapter is transport-agnostic. It binds a commit to the exact MCP
execution tuple and, when supplied, the execution identity/binding context.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from threading import Lock
from typing import Any


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def request_digest(tool_name: str, arguments: dict[str, Any]) -> str:
    return _sha256_json({"tool_name": tool_name, "arguments": arguments})


def action_binding_digest(
    *,
    agent_identity: str,
    execution_id: str,
    tool_name: str,
    request_payload_hash: str,
    policy_id: str,
) -> str:
    """Digest the immutable action-binding tuple used by the execution gate."""
    return _sha256_json(
        {
            "agent_identity": agent_identity,
            "execution_id": execution_id,
            "tool_name": tool_name,
            "request_payload_hash": request_payload_hash,
            "policy_id": policy_id,
        }
    )


@dataclass(frozen=True)
class EABCCommit:
    commit_id: str
    call_id: str
    tool_name: str
    request_payload_hash: str
    policy_id: str
    agent_identity: str | None = None
    execution_id: str | None = None
    action_binding: str | None = None
    authority_ref: str | None = None
    authority_epoch: int | None = None


class EABCMCPAdapter:
    """Bind and consume EABC commits for an MCP execution attempt."""

    def __init__(self) -> None:
        self._consumed: set[str] = set()
        self._lock = Lock()

    def validate(
        self,
        commit: EABCCommit,
        *,
        call_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        policy_id: str,
        agent_identity: str | None = None,
        execution_id: str | None = None,
        current_authority_epoch: int | None = None,
    ) -> None:
        with self._lock:
            if commit.commit_id in self._consumed:
                raise PermissionError("EABC_COMMIT_REPLAY")

            digest = request_digest(tool_name, arguments)
            binding = None
            if agent_identity is not None and execution_id is not None:
                binding = action_binding_digest(
                    agent_identity=agent_identity,
                    execution_id=execution_id,
                    tool_name=tool_name,
                    request_payload_hash=digest,
                    policy_id=policy_id,
                )

            candidate = EABCCommit(
                commit_id=commit.commit_id,
                call_id=call_id,
                tool_name=tool_name,
                request_payload_hash=digest,
                policy_id=policy_id,
                agent_identity=agent_identity,
                execution_id=execution_id,
                action_binding=binding,
                authority_ref=commit.authority_ref,
                authority_epoch=commit.authority_epoch,
            )
            if candidate != commit:
                raise PermissionError("EABC_COMMIT_SUBSTITUTION")

            if (
                current_authority_epoch is not None
                and commit.authority_epoch is not None
                and commit.authority_epoch != current_authority_epoch
            ):
                raise PermissionError("EABC_AUTHORITY_EPOCH_MISMATCH")

            self._consumed.add(commit.commit_id)
