import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=["docs/041-t27-scope.md","docs/042-t27-interoperability-vectors.md","docs/043-t27-reproducibility.md","docs/044-t27-evidence.md","docs/045-t27-boundary.md","evidence/t27-test-vectors.json","evidence/t27-provenance.json"]
def main():
    d={"manifest_id":"eabc-mcp-t27","profile_id":"eabc-mcp","profile_version":"0.1-experimental","result":"REPRODUCIBLE_INTEROPERABILITY","hash_algorithm":"SHA-256","git_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"artifacts":[{"path":p,"sha256":"sha256:"+hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in FILES]}
    (ROOT/"evidence/t27-reproduction-manifest.json").write_text(json.dumps(d,sort_keys=True,indent=2)+"\n")
if __name__=="__main__": main()
