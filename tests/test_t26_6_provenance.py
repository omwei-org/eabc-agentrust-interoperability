"""T26.6 — provenance manifest integrity checks."""

import json
from pathlib import Path


def test_t26_6_provenance_is_pinned():
    data = json.loads(
        Path("evidence/t26-6-provenance.json").read_text(encoding="utf-8")
    )
    assert data["upstream"]["source_revision"] == "d03b9af504535d3d43f192bc6d9eff89b8afd12f"
    assert data["adapter"]["validated_revision"] == "c367837f504f19561192cdd9d98ef4a91497a5f2"
    assert data["integrity"]["method"] == "sha256"


def test_t26_6_ci_references_are_concrete():
    data = json.loads(
        Path("evidence/t26-6-provenance.json").read_text(encoding="utf-8")
    )
    assert all(
        isinstance(v, str) and v.isdigit()
        for v in data["ci"].values()
    )
