"""T29.4 execution-admission harness.

Protocol harness for the proposed EABC gate at the cMCP execution-admission
boundary. This is not a claim of native cMCP EABC enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from .adapter import EABCCommit, EABCMCPAdapter


@dataclass(frozen=True)
class ExecutionReservation:
    agent_identity: str
    execution_id: str
    action_binding: str


class ExecutionAdmission:
    """Model reservation, COMMIT validation, and terminal-state handling."""

    def __init__(self) -> None:
        self._reservations: dict[tuple[str, str], ExecutionReservation] = {}
        self._terminal: set[str] = set()
        self._unknown: set[str] = set()
        self._adapter = EABCMCPAdapter()

    def reserve(self, *, agent_identity: str, execution_id: str, action_binding: str) -> None:
        key = (agent_identity, execution_id)
        existing = self._reservations.get(key)
        candidate = ExecutionReservation(agent_identity, execution_id, action_binding)
        if existing is None:
            self._reservations[key] = candidate
            return
        if existing != candidate:
            raise PermissionError("EABC_EXECUTION_RESERVATION_CONFLICT")

    def commit(self, commit: EABCCommit, *, agent_identity: str, execution_id: str,
               call_id: str, tool_name: str, arguments: dict, policy_id: str) -> None:
        reservation = self._reservations.get((agent_identity, execution_id))
        if reservation is None:
            raise PermissionError("EABC_NO_EXECUTION_RESERVATION")
        if reservation.action_binding != commit.action_binding:
            raise PermissionError("EABC_EXECUTION_BINDING_MISMATCH")
        if commit.commit_id in self._terminal or commit.commit_id in self._unknown:
            raise PermissionError("EABC_REPLAY_AFTER_OUTCOME")
        self._adapter.validate(
            commit,
            agent_identity=agent_identity,
            execution_id=execution_id,
            call_id=call_id,
            tool_name=tool_name,
            arguments=arguments,
            policy_id=policy_id,
        )

    def mark_terminal(self, commit_id: str) -> None:
        self._terminal.add(commit_id)

    def mark_outcome_unknown(self, commit_id: str) -> None:
        self._unknown.add(commit_id)

    def forwarding_allowed(self, commit: EABCCommit) -> bool:
        return commit.commit_id not in self._terminal and commit.commit_id not in self._unknown
