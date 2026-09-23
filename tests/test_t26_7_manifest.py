from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evidence/t26-7-evidence-manifest.json"

def test_t26_7_manifest_is_self_consistent():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["manifest_id"] == "eabc-mcp-t26-7"
    assert data["hash_algorithm"] == "SHA-256"
    for item in data["artifacts"]:
        path = ROOT / item["path"]
        actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == item["sha256"]

def test_t26_7_manifest_contains_required_profile_artifacts():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = {x["path"] for x in data["artifacts"]}
    assert "evidence/t26-5-conformance-bundle.json" in paths
    assert "evidence/t26-6-provenance.json" in paths
    assert "docs/036-t26-eabc-mcp-profile.md" in paths
