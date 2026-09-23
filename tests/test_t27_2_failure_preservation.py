from eabc_profile import EABCCommit,EABCMCPAdapter
from eabc_profile.adapter import request_digest
import pytest

def test_downstream_failure_is_not_reported_as_applied():
    a=EABCMCPAdapter(); applied=[]
    args={"destination":"cell-3"}
    c=EABCCommit("t27-failure-001","call-27-failure","move",request_digest("move",args),"policy-A")
    def execute():
        a.validate(c,call_id="call-27-failure",tool_name="move",arguments=args,policy_id="policy-A")
        raise RuntimeError("DOWNSTREAM_EXECUTION_FAILURE")
    with pytest.raises(RuntimeError,match="DOWNSTREAM_EXECUTION_FAILURE"):
        execute()
    assert applied==[]

def test_failed_execution_cannot_replay_commit():
    a=EABCMCPAdapter(); args={"destination":"cell-3"}
    c=EABCCommit("t27-failure-002","call-27-failure","move",request_digest("move",args),"policy-A")
    a.validate(c,call_id="call-27-failure",tool_name="move",arguments=args,policy_id="policy-A")
    with pytest.raises(PermissionError,match="EABC_COMMIT_REPLAY"):
        a.validate(c,call_id="call-27-failure",tool_name="move",arguments=args,policy_id="policy-A")
