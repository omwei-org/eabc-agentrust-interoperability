from __future__ import annotations

import pytest

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import action_binding_digest, request_digest


def make_commit(*, args=None, call_id="call-001") -> EABCCommit:
    args = {"x": 1} if args is None else args
    agent = "agent-A"
    execution_id = "exec-001"
    tool = "test.echo"
    policy = "policy-A"
    request_hash = request_digest(tool, args)
    return EABCCommit(
        commit_id="commit-001",
        agent_identity=agent,
        execution_id=execution_id,
        call_id=call_id,
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


def test_t29_3_exact_execution_binding_is_accepted():
    adapter = EABCMCPAdapter()
    commit = make_commit()

    adapter.validate(
        commit,
        agent_identity="agent-A",
        execution_id="exec-001",
        call_id="call-001",
        tool_name="test.echo",
        arguments={"x": 1},
        policy_id="policy-A",
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("agent_identity", "agent-B"),
        ("execution_id", "exec-002"),
        ("call_id", "call-002"),
        ("tool_name", "test.other"),
        ("policy_id", "policy-B"),
    ],
)
def test_t29_3_substitution_is_rejected(field: str, value: str):
    adapter = EABCMCPAdapter()
    commit = make_commit()
    kwargs = {
        "agent_identity": "agent-A",
        "execution_id": "exec-001",
        "call_id": "call-001",
        "tool_name": "test.echo",
        "arguments": {"x": 1},
        "policy_id": "policy-A",
    }
    kwargs[field] = value

    with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
        adapter.validate(commit, **kwargs)


def test_t29_3_request_substitution_is_rejected():
    adapter = EABCMCPAdapter()
    commit = make_commit(args={"x": 1})

    with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
        adapter.validate(
            commit,
            agent_identity="agent-A",
            execution_id="exec-001",
            call_id="call-001",
            tool_name="test.echo",
            arguments={"x": 2},
            policy_id="policy-A",
        )


def test_t29_3_commit_is_single_use():
    adapter = EABCMCPAdapter()
    commit = make_commit()

    kwargs = {
        "agent_identity": "agent-A",
        "execution_id": "exec-001",
        "call_id": "call-001",
        "tool_name": "test.echo",
        "arguments": {"x": 1},
        "policy_id": "policy-A",
    }
    adapter.validate(commit, **kwargs)

    with pytest.raises(PermissionError, match="EABC_COMMIT_REPLAY"):
        adapter.validate(commit, **kwargs)
