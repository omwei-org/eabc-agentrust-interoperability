"""T30 contract fixtures: the proposed cMCP/EABC admission seam."""

from eabc_profile.adapter import action_binding_digest, request_digest
from eabc_profile import EABCCommit

def make_t30_commit():
    agent = "agent-A"
    execution = "exec-001"
    call_id = "call-001"
    tool = "test.echo"
    arguments = {"x": 1}
    policy = "policy-A"
    request_hash = request_digest(tool, arguments)
    binding = action_binding_digest(
        agent_identity=agent, execution_id=execution, tool_name=tool,
        request_payload_hash=request_hash, policy_id=policy,
    )
    return EABCCommit(
        commit_id="commit-001", agent_identity=agent, execution_id=execution,
        call_id=call_id, tool_name=tool, request_payload_hash=request_hash,
        policy_id=policy, action_binding=binding, authority_ref="authority-001",
    )

def test_t30_commit_contains_forwarding_admission_binding():
    commit = make_t30_commit()
    assert commit.agent_identity == "agent-A"
    assert commit.execution_id == "exec-001"
    assert commit.call_id == "call-001"
    assert commit.tool_name == "test.echo"
    assert commit.request_payload_hash.startswith("sha256:")
    assert commit.policy_id == "policy-A"
    assert commit.action_binding.startswith("sha256:")
    assert commit.authority_ref == "authority-001"