from __future__ import annotations

import hashlib
import json


def payload_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_t25_real_cmcp_forwarding_symbol_is_importable():
    from cmcp.gateway.proxy import CMCPProxy

    assert hasattr(CMCPProxy, "_forward_to_upstream")
    assert hasattr(CMCPProxy, "call_tool")


def test_t25_real_forwarding_seam_accepts_eabc_gate(monkeypatch):
    from cmcp.gateway.proxy import CMCPProxy

    seen = []
    original = CMCPProxy._forward_to_upstream

    def gated(self, call_id, entry, tool_name, arguments):
        commit = getattr(self, "_t25_commit", None)
        if commit is None:
            raise RuntimeError("T25_NO_COMMIT")
        if commit["call_id"] != call_id:
            raise RuntimeError("T25_CALL_ID_MISMATCH")
        if commit["tool_name"] != tool_name:
            raise RuntimeError("T25_TOOL_MISMATCH")
        if commit["request_payload_hash"] != payload_hash(arguments):
            raise RuntimeError("T25_REQUEST_DIGEST_MISMATCH")
        seen.append((call_id, tool_name, arguments))
        return original(self, call_id, entry, tool_name, arguments)

    monkeypatch.setattr(CMCPProxy, "_forward_to_upstream", gated)
    assert CMCPProxy._forward_to_upstream is gated
    assert seen == []


def test_t25_commit_binding_fields_are_machine_checkable():
    arguments = {"destination": "cell-3", "speed": 0.2}
    commit = {
        "commit_id": "t25-runtime-1",
        "call_id": "call-1",
        "tool_name": "move",
        "request_payload_hash": payload_hash(arguments),
    }

    assert commit["request_payload_hash"] == payload_hash(arguments)
    assert commit["call_id"] == "call-1"
    assert commit["tool_name"] == "move"
