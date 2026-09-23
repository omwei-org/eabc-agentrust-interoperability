"""Build a content-addressed T26.7 evidence manifest."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "docs/036-t26-eabc-mcp-profile.md",
    "docs/037-t26-profile-conformance.md",
    "docs/038-t26-4-conformance-result.md",
    "docs/039-t26-5-evidence-bundle.md",
    "evidence/t26-5-conformance-bundle.json",
    "evidence/t26-6-provenance.json",
]
OUT = ROOT / "evidence/t26-7-evidence-manifest.json"

def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    entries = [{"path": p, "sha256": sha256(ROOT / p)} for p in FILES]
    manifest = {
        "manifest_id": "eabc-mcp-t26-7",
        "profile_id": "eabc-mcp",
        "profile_version": "0.1-experimental",
        "hash_algorithm": "SHA-256",
        "artifacts": entries,
    }
    OUT.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
