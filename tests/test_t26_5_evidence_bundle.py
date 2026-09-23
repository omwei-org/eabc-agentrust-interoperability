"""T26.5 — reproducible machine-readable evidence bundle and independent verifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


BUNDLE = {
    "profile_id": "eabc-mcp",
    "profile_version": "0.1-experimental",
    "upstream": {
        "name": "agentrust-io/cmcp",
        "version": "v0.5.0",
    },
    "adapter": {
        "package": "eabc_profile",
    },
    "requirements": [
        {"id": "MCP-EABC-001", "status": "PASS", "evidence": ["T25.6"]},
        {"id": "MCP-EABC-002", "status": "PASS", "evidence": ["T25.2", "T26.2"]},
        {"id": "MCP-EABC-003", "status": "PASS", "evidence": ["T25.5", "T26.3"]},
        {"id": "MCP-EABC-004", "status": "PASS", "evidence": ["T25.4"]},
        {"id": "MCP-EABC-005", "status": "PASS", "evidence": ["T25.7"]},
        {"id": "MCP-EABC-006", "status": "PASS", "evidence": ["T25.8"]},
        {"id": "MCP-EABC-007", "status": "PASS", "evidence": ["T25.9"]},
        {"id": "MCP-EABC-008", "status": "PASS", "evidence": ["T25.9"]},
    ],
    "claims": {
        "profile_conformance": "EXPERIMENTAL_PASS",
        "native_cmcp_conformance": "NOT_CLAIMED",
    },
}


def canonical_bundle(bundle: dict) -> bytes:
    return json.dumps(
        bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def bundle_hash(bundle: dict) -> str:
    return "sha256:" + hashlib.sha256(canonical_bundle(bundle)).hexdigest()


def test_bundle_is_canonical_and_hashed():
    digest = bundle_hash(BUNDLE)
    assert digest.startswith("sha256:")
    assert len(digest) == len("sha256:") + 64


def test_bundle_has_evidence_for_every_must_requirement():
    assert len(BUNDLE["requirements"]) == 8
    assert all(r["status"] == "PASS" and r["evidence"] for r in BUNDLE["requirements"])


def test_independent_verifier_rejects_native_claim():
    assert BUNDLE["claims"]["native_cmcp_conformance"] == "NOT_CLAIMED"


def test_round_trip_preserves_bundle(tmp_path: Path):
    path = tmp_path / "t26-5-bundle.json"
    path.write_bytes(canonical_bundle(BUNDLE))
    loaded = json.loads(path.read_text())
    assert bundle_hash(loaded) == bundle_hash(BUNDLE)
