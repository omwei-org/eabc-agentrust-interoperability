from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import request_digest
import pytest

def commit_for():
    return EABCCommit("t27-valid-001","call-27-001","test.echo",request_digest("test.echo",{"x":1}),"policy-A")

def test_valid_vector_is_accepted():
    EABCMCPAdapter().validate(commit_for(),call_id="call-27-001",tool_name="test.echo",arguments={"x":1},policy_id="policy-A")

@pytest.mark.parametrize(("call_id","tool_name","arguments","policy_id"),[
    ("call-27-other","test.echo",{"x":1},"policy-A"),
    ("call-27-001","test.other",{"x":1},"policy-A"),
    ("call-27-001","test.echo",{"x":2},"policy-A"),
    ("call-27-001","test.echo",{"x":1},"policy-B"),
])
def test_exact_tuple_substitution_is_rejected(call_id,tool_name,arguments,policy_id):
    with pytest.raises(PermissionError,match="EABC_COMMIT_SUBSTITUTION"):
        EABCMCPAdapter().validate(commit_for(),call_id=call_id,tool_name=tool_name,arguments=arguments,policy_id=policy_id)

def test_replay_is_rejected():
    a=EABCMCPAdapter(); c=commit_for()
    a.validate(c,call_id="call-27-001",tool_name="test.echo",arguments={"x":1},policy_id="policy-A")
    with pytest.raises(PermissionError,match="EABC_COMMIT_REPLAY"):
        a.validate(c,call_id="call-27-001",tool_name="test.echo",arguments={"x":1},policy_id="policy-A")
