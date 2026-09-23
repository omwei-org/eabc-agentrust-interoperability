from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evidence/t26-7-evidence-manifest.json"

REQUIRED_ARTIFACTS = {
    "docs/036-t26-eabc-mcp-profile.md",
    "docs/037-t26-profile-conformance.md",
    "docs/038-t26-4-conformance-result.md",
    "docs/039-t26-5-evidence-bundle.md",
    "evidence/t26-5-conformance-bundle.json",
    "evidence/t26-6-provenance.json",
}

def test_t26_7_manifest_is_self_consistent():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["manifest_id"] == "eabc-mcp-t26-7"
    assert data["hash_algorithm"] == "SHA-256"
    assert re.fullmatch(r"[0-9a-f]{40}", data["git_commit"])
    assert len(data["artifacts"]) == len(REQUIRED_ARTIFACTS)
    for item in data["artifacts"]:
        assert item["path"] in REQUIRED_ARTIFACTS
        path = ROOT / item["path"]
        actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == item["sha256"]

def test_t26_7_manifest_contains_required_profile_artifacts():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = {x["path"] for x in data["artifacts"]}
    assert paths == REQUIRED_ARTIFACTS
