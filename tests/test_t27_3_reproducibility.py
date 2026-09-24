import json
from eabc_profile import EABCCommit,EABCMCPAdapter
from eabc_profile.adapter import request_digest

V=(("valid","call-1","test.echo",{"x":1},"policy-A"),("tool","call-1","test.other",{"x":1},"policy-A"),("request","call-1","test.echo",{"x":2},"policy-A"),("policy","call-1","test.echo",{"x":1},"policy-B"))

def run():
    out=[]
    for name,call,tool,args,policy in V:
        a=EABCMCPAdapter(); c=EABCCommit("t27-repro","call-1","test.echo",request_digest("test.echo",{"x":1}),"policy-A")
        try:
            a.validate(c,call_id=call,tool_name=tool,arguments=args,policy_id=policy); ok=True; err=None
        except PermissionError as e:
            ok=False; err=str(e)
        out.append({"vector":name,"accepted":ok,"error":err})
    return out

def test_repeated_runs_are_identical():
    assert run()==run()
    assert json.dumps(run(),sort_keys=True,separators=(",",":"))==json.dumps(run(),sort_keys=True,separators=(",",":"))

def test_expected_results():
    assert [x["accepted"] for x in run()]==[True,False,False,False]
