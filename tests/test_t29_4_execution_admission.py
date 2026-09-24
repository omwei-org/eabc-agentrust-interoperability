from __future__ import annotations

import pytest

from eabc_profile import EABCCommit, action_binding_digest
from eabc_profile.adapter import request_digest
from eabc_profile.admission import ExecutionAdmission


def make_commit(*, execution_id="exec-001", args=None) -> EABCCommit:
    args = {"x": 1} if args is None else args
    agent = "agent-A"
    tool = "test.echo"
    policy = "policy-A"
    request_hash = request_digest(tool, args)
    return EABCCommit(
        commit_id="commit-001",
        agent_identity=agent,
        execution_id=execution_id,
        call_id="call-001",
        tool_name=tool,
        request_payload_hash=request_hash,
        policy_id=policy,
        action_binding=action_binding_digest(
            agent_identity=agent,
            execution_id=execution_id,
            tool_name=tool,
            request_payload_hash=request_hash,
            policy_id=policy,
        ),
        authority_ref="authority-001",
    )


def admit(admission, commit):
    admission.reserve(
        agent_identity=commit.agent_identity,
        execution_id=commit.execution_id,
        action_binding=commit.action_binding,
    )


def test_t29_4_no_commit_has_no_forwarding_authority():
    admission = ExecutionAdmission()
    commit = make_commit()
    with pytest.raises(PermissionError, match="EABC_NO_EXECUTION_RESERVATION"):
        admission.commit(
            commit, agent_identity="agent-A", execution_id="exec-001",
            call_id="call-001", tool_name="test.echo", arguments={"x": 1},
            policy_id="policy-A",
        )


def test_t29_4_exact_commit_allows_one_admission():
    admission = ExecutionAdmission()
    commit = make_commit()
    admit(admission, commit)
    admission.commit(
        commit, agent_identity="agent-A", execution_id="exec-001",
        call_id="call-001", tool_name="test.echo", arguments={"x": 1},
        policy_id="policy-A",
    )


def test_t29_4_substituted_execution_id_is_rejected():
    admission = ExecutionAdmission()
    commit = make_commit()
    admit(admission, commit)
    with pytest.raises(PermissionError, match="EABC_NO_EXECUTION_RESERVATION"):
        admission.commit(
            commit, agent_identity="agent-A", execution_id="exec-002",
            call_id="call-001", tool_name="test.echo", arguments={"x": 1},
            policy_id="policy-A",
        )


def test_t29_4_substituted_action_is_rejected():
    admission = ExecutionAdmission()
    original = make_commit()
    admit(admission, original)
    substituted = make_commit(args={"x": 2})
    with pytest.raises(PermissionError):
        admission.commit(
            substituted, agent_identity="agent-A", execution_id="exec-001",
            call_id="call-001", tool_name="test.echo", arguments={"x": 2},
            policy_id="policy-A",
        )


def test_t29_4_replay_after_terminal_outcome_is_rejected():
    admission = ExecutionAdmission()
    commit = make_commit()
    admit(admission, commit)
    admission.mark_terminal(commit.commit_id)
    with pytest.raises(PermissionError, match="EABC_REPLAY_AFTER_OUTCOME"):
        admission.commit(
            commit, agent_identity="agent-A", execution_id="exec-001",
            call_id="call-001", tool_name="test.echo", arguments={"x": 1},
            policy_id="policy-A",
        )


def test_t29_4_outcome_unknown_is_not_replay_permission():
    admission = ExecutionAdmission()
    commit = make_commit()
    admit(admission, commit)
    admission.mark_outcome_unknown(commit.commit_id)
    with pytest.raises(PermissionError, match="EABC_REPLAY_AFTER_OUTCOME"):
        admission.commit(
            commit, agent_identity="agent-A", execution_id="exec-001",
            call_id="call-001", tool_name="test.echo", arguments={"x": 1},
            policy_id="policy-A",
        )


def test_t29_4_conflicting_reservation_is_rejected():
    admission = ExecutionAdmission()
    commit = make_commit()
    admit(admission, commit)
    conflicting = make_commit(execution_id="exec-002")
    with pytest.raises(PermissionError, match="EABC_EXECUTION_RESERVATION_CONFLICT"):
        admission.reserve(
            agent_identity="agent-A",
            execution_id="exec-001",
            action_binding=conflicting.action_binding,
        )
