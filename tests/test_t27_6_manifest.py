import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; MANIFEST=ROOT/"evidence/t27-reproduction-manifest.json"
REQ={"docs/041-t27-scope.md","docs/042-t27-interoperability-vectors.md","docs/043-t27-reproducibility.md","docs/044-t27-evidence.md","docs/045-t27-boundary.md","evidence/t27-test-vectors.json","evidence/t27-provenance.json"}
def test_manifest_binds_exact_files():
    d=json.loads(MANIFEST.read_text())
    assert d["manifest_id"]=="eabc-mcp-t27" and d["result"]=="REPRODUCIBLE_INTEROPERABILITY"
    assert re.fullmatch(r"[0-9a-f]{40}",d["git_commit"])
    assert {x["path"] for x in d["artifacts"]}==REQ
    for x in d["artifacts"]:
        assert x["sha256"]=="sha256:"+hashlib.sha256((ROOT/x["path"]).read_bytes()).hexdigest()
