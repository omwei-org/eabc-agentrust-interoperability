from __future__ import annotations

import hashlib
import json


def digest(value):
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class IndependentBoundary:
    def __init__(self):
        self.effects = []
        self.used = set()

    def prepare(self, *, commit_id, call_id, tool_name, arguments, epoch):
        return {
            "commit_id": commit_id,
            "call_id": call_id,
            "tool_name": tool_name,
            "request_payload_hash": digest(arguments),
            "authority_epoch": epoch,
        }

    def commit(self, token, *, call_id, tool_name, arguments, current_epoch):
        if token is None:
            return "NO_COMMIT"
        if token["commit_id"] in self.used:
            return "REPLAY"
        if token["call_id"] != call_id:
            return "CALL_ID_MISMATCH"
        if token["tool_name"] != tool_name:
            return "TOOL_MISMATCH"
        if token["request_payload_hash"] != digest(arguments):
            return "REQUEST_DIGEST_MISMATCH"
        if token["authority_epoch"] != current_epoch:
            return "STALE_EPOCH"
        self.used.add(token["commit_id"])
        self.effects.append({"call_id": call_id, "tool_name": tool_name, "arguments": arguments.copy()})
        return "COMMITTED"


def test_t25_valid_commit_effect():
    b = IndependentBoundary()
    args = {"destination": "cell-3"}
    t = b.prepare(commit_id="t25-1", call_id="c1", tool_name="move", arguments=args, epoch=7)
    assert b.commit(t, call_id="c1", tool_name="move", arguments=args, current_epoch=7) == "COMMITTED"
    assert len(b.effects) == 1


def test_t25_tampered_request_no_effect():
    b = IndependentBoundary()
    args = {"destination": "cell-3"}
    t = b.prepare(commit_id="t25-2", call_id="c2", tool_name="move", arguments=args, epoch=7)
    assert b.commit(t, call_id="c2", tool_name="move", arguments={"destination": "cell-9"}, current_epoch=7) == "REQUEST_DIGEST_MISMATCH"
    assert b.effects == []


def test_t25_stale_authority_no_effect():
    b = IndependentBoundary()
    args = {"destination": "cell-3"}
    t = b.prepare(commit_id="t25-3", call_id="c3", tool_name="move", arguments=args, epoch=7)
    assert b.commit(t, call_id="c3", tool_name="move", arguments=args, current_epoch=8) == "STALE_EPOCH"
    assert b.effects == []


def test_t25_replay_no_second_effect():
    b = IndependentBoundary()
    args = {"destination": "cell-3"}
    t = b.prepare(commit_id="t25-4", call_id="c4", tool_name="move", arguments=args, epoch=7)
    assert b.commit(t, call_id="c4", tool_name="move", arguments=args, current_epoch=7) == "COMMITTED"
    assert b.commit(t, call_id="c4", tool_name="move", arguments=args, current_epoch=7) == "REPLAY"
    assert len(b.effects) == 1
