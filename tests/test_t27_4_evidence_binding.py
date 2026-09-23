import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_vectors_are_unique_and_complete():
    d=json.loads((ROOT/"evidence/t27-test-vectors.json").read_text()); ids=[x["id"] for x in d["vectors"]]
    assert len(ids)==len(set(ids)) and len(ids)>=7
def test_provenance_is_pinned():
    d=json.loads((ROOT/"evidence/t27-provenance.json").read_text())
    assert d["upstream"]["source_revision"]=="d03b9af504535d3d43f192bc6d9eff89b8afd12f"
    assert re.fullmatch(r"[0-9a-f]{40}",d["base_repository_revision"])
