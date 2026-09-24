from __future__ import annotations

import pytest

from eabc_profile import EABCCommit, action_binding_digest
from eabc_profile.adapter import request_digest
from eabc_profile.admission import ExecutionAdmission


def make_commit(args=None):
    args = {"x": 1} if args is None else args
    agent = "agent-A"
    execution = "exec-001"
    tool = "test.echo"
    request_hash = request_digest(tool, args)
    return EABCCommit(
        commit_id="commit-001",
        agent_identity=agent,
        execution_id=execution,
        call_id="call-001",
        tool_name=tool,
        request_payload_hash=request_hash,
        policy_id="policy-A",
        action_binding=action_binding_digest(
            agent_identity=agent,
            execution_id=execution,
            tool_name=tool,
            request_payload_hash=request_hash,
            policy_id="policy-A",
        ),
        authority_ref="authority-001",
    )


def run_forwarding(commit, args, *, execution_id="exec-001", admit=True):
    admission = ExecutionAdmission()
    effects = []

    if admit:
        admission.reserve(
            agent_identity="agent-A",
            execution_id=commit.execution_id,
            action_binding=commit.action_binding,
        )

    admission.commit(
        commit,
        agent_identity="agent-A",
        execution_id=execution_id,
        call_id="call-001",
        tool_name="test.echo",
        arguments=args,
        policy_id="policy-A",
    )
    effects.append(args)
    return effects


def test_t30_2_exact_commit_reaches_consequence_once():
    commit = make_commit()
    effects = run_forwarding(commit, {"x": 1})
    assert effects == [{"x": 1}]


def test_t30_2_missing_commit_never_reaches_consequence():
    commit = make_commit()
    with pytest.raises(PermissionError, match="EABC_NO_EXECUTION_RESERVATION"):
        run_forwarding(commit, {"x": 1}, admit=False)


def test_t30_2_substituted_execution_id_never_reaches_consequence():
    commit = make_commit()
    with pytest.raises(PermissionError, match="EABC_NO_EXECUTION_RESERVATION"):
        run_forwarding(commit, {"x": 1}, execution_id="exec-002")


def test_t30_2_substituted_request_never_reaches_consequence():
    commit = make_commit()
    with pytest.raises(PermissionError):
        run_forwarding(commit, {"x": 2})


def test_t30_2_terminal_commit_never_reaches_consequence():
    commit = make_commit()
    admission = ExecutionAdmission()
    admission.reserve(
        agent_identity=commit.agent_identity,
        execution_id=commit.execution_id,
        action_binding=commit.action_binding,
    )
    admission.mark_terminal(commit.commit_id)
    with pytest.raises(PermissionError, match="EABC_REPLAY_AFTER_OUTCOME"):
        admission.commit(
            commit,
            agent_identity="agent-A",
            execution_id="exec-001",
            call_id="call-001",
            tool_name="test.echo",
            arguments={"x": 1},
            policy_id="policy-A",
        )
