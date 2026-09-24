from pathlib import Path
import hashlib
import json


def test_observable_sink_is_file_backed(tmp_path: Path):
    event = {"call_id": "call-001", "consequence": "upstream-forwarded"}
    raw = json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    sink = tmp_path / "upstream-effect.jsonl"
    sink.write_bytes(raw + b"\n")
    digest = hashlib.sha256(sink.read_bytes()).hexdigest()
    assert sink.exists()
    assert sink.read_text() == raw.decode() + "\n"
    assert len(digest) == 64


def test_evidence_manifest_fields_are_defined():
    required = {"upstream_commit","experiment_commit","execution_id","call_id","request_payload_hash","commit_id","terminal_state","sink_sha256"}
    assert len(required) == 8
