from dataclasses import replace

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import action_binding_digest, request_digest
import pytest


def make_commit():
    agent_identity = "agent-A"
    execution_id = "exec-001"
    tool_name = "test.echo"
    arguments = {"x": 1}
    policy_id = "policy-A"
    payload_hash = request_digest(tool_name, arguments)
    binding = action_binding_digest(
        agent_identity=agent_identity,
        execution_id=execution_id,
        tool_name=tool_name,
        request_payload_hash=payload_hash,
        policy_id=policy_id,
    )
    return EABCCommit(
        commit_id="eabc-t26-001",
        agent_identity=agent_identity,
        execution_id=execution_id,
        call_id="call-001",
        tool_name=tool_name,
        request_payload_hash=payload_hash,
        policy_id=policy_id,
        action_binding=binding,
        authority_ref="authority-A",
    )


def test_valid_commit_is_accepted_once():
    adapter = EABCMCPAdapter()
    adapter.validate(
        make_commit(),
        agent_identity="agent-A",
        execution_id="exec-001",
        call_id="call-001",
        tool_name="test.echo",
        arguments={"x": 1},
        policy_id="policy-A",
    )
    with pytest.raises(PermissionError, match="EABC_COMMIT_REPLAY"):
        adapter.validate(
            make_commit(),
            agent_identity="agent-A",
            execution_id="exec-001",
            call_id="call-001",
            tool_name="test.echo",
            arguments={"x": 1},
            policy_id="policy-A",
        )


@pytest.mark.parametrize(
    "agent_identity,execution_id,call_id,tool_name,arguments,policy_id",
    [
        ("agent-B", "exec-001", "call-001", "test.echo", {"x": 1}, "policy-A"),
        ("agent-A", "exec-002", "call-001", "test.echo", {"x": 1}, "policy-A"),
        ("agent-A", "exec-001", "call-002", "test.echo", {"x": 1}, "policy-A"),
        ("agent-A", "exec-001", "call-001", "test.other", {"x": 1}, "policy-A"),
        ("agent-A", "exec-001", "call-001", "test.echo", {"x": 2}, "policy-A"),
        ("agent-A", "exec-001", "call-001", "test.echo", {"x": 1}, "policy-B"),
    ],
)
def test_substitution_is_rejected(
    agent_identity, execution_id, call_id, tool_name, arguments, policy_id
):
    adapter = EABCMCPAdapter()
    with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
        adapter.validate(
            make_commit(),
            agent_identity=agent_identity,
            execution_id=execution_id,
            call_id=call_id,
            tool_name=tool_name,
            arguments=arguments,
            policy_id=policy_id,
        )


def test_action_binding_substitution_is_rejected():
    adapter = EABCMCPAdapter()
    tampered = replace(make_commit(), action_binding="sha256:" + "0" * 64)
    with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
        adapter.validate(
            tampered,
            agent_identity="agent-A",
            execution_id="exec-001",
            call_id="call-001",
            tool_name="test.echo",
            arguments={"x": 1},
            policy_id="policy-A",
        )
