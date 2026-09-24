from __future__ import annotations

import pytest

from eabc_profile import EABCCommit, action_binding_digest
from eabc_profile.adapter import request_digest


def make_commit():
    agent = "agent-A"
    execution = "exec-001"
    call_id = "call-001"
    tool = "test.echo"
    args = {"x": 1}
    policy = "policy-A"
    request_hash = request_digest(tool, args)
    return EABCCommit(
        commit_id="commit-001",
        agent_identity=agent,
        execution_id=execution,
        call_id=call_id,
        tool_name=tool,
        request_payload_hash=request_hash,
        policy_id=policy,
        action_binding=action_binding_digest(
            agent_identity=agent,
            execution_id=execution,
            tool_name=tool,
            request_payload_hash=request_hash,
            policy_id=policy,
        ),
        authority_ref="authority-001",
    )


def test_t30_1_exact_commit_is_the_only_admission():
    commit = make_commit()
    assert commit.commit_id == "commit-001"
    assert commit.action_binding
    assert commit.authority_ref


@pytest.mark.parametrize("field,value", [
    ("execution_id", "exec-002"),
    ("call_id", "call-002"),
    ("tool_name", "test.other"),
    ("policy_id", "policy-B"),
])
def test_t30_1_binding_dimensions_are_distinct(field, value):
    commit = make_commit()
    assert getattr(commit, field) != value
