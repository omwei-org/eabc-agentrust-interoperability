from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import request_digest
import pytest


def make_commit():
    return EABCCommit(
        commit_id="eabc-t26-001",
        call_id="call-001",
        tool_name="test.echo",
        request_payload_hash=request_digest("test.echo", {"x": 1}),
        policy_id="policy-A",
    )


def test_valid_commit_is_accepted_once():
    adapter = EABCMCPAdapter()
    adapter.validate(
        make_commit(),
        call_id="call-001",
        tool_name="test.echo",
        arguments={"x": 1},
        policy_id="policy-A",
    )
    with pytest.raises(PermissionError, match="EABC_COMMIT_REPLAY"):
        adapter.validate(
            make_commit(),
            call_id="call-001",
            tool_name="test.echo",
            arguments={"x": 1},
            policy_id="policy-A",
        )


@pytest.mark.parametrize(
    "call_id,tool_name,arguments,policy_id",
    [
        ("call-002", "test.echo", {"x": 1}, "policy-A"),
        ("call-001", "test.other", {"x": 1}, "policy-A"),
        ("call-001", "test.echo", {"x": 2}, "policy-A"),
        ("call-001", "test.echo", {"x": 1}, "policy-B"),
    ],
)
def test_substitution_is_rejected(call_id, tool_name, arguments, policy_id):
    adapter = EABCMCPAdapter()
    with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
        adapter.validate(
            make_commit(),
            call_id=call_id,
            tool_name=tool_name,
            arguments=arguments,
            policy_id=policy_id,
        )
