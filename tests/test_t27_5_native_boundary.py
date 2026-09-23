import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_native_conformance_remains_unclaimed():
    b=json.loads((ROOT/"evidence/t26-5-conformance-bundle.json").read_text())
    p=json.loads((ROOT/"evidence/t27-provenance.json").read_text())
    assert b["claims"]["profile_conformance"]=="EXPERIMENTAL_PASS"
    assert b["claims"]["native_cmcp_conformance"]=="NOT_CLAIMED"
    assert p["claims"]["native_cmcp_conformance"]=="NOT_CLAIMED"
