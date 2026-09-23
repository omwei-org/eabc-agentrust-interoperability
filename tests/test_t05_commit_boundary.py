from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import pytest


def digest(request: dict) -> str:
    body = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(body).hexdigest()


@dataclass
class Boundary:
    authority_epoch: int = 1

    def prepare(self, request: dict) -> dict:
        return {"request": request, "request_digest": digest(request), "epoch": self.authority_epoch}

    def commit(self, prepared: dict, request: dict | None = None) -> dict:
        candidate = prepared["request"] if request is None else request
        if prepared["epoch"] != self.authority_epoch:
            raise PermissionError("STALE_AUTHORITY_EPOCH")
        if digest(candidate) != prepared["request_digest"]:
            raise PermissionError("REQUEST_SUBSTITUTION")
        return {
            "commit_id": "commit-" + prepared["request_digest"][7:23],
            "request_digest": prepared["request_digest"],
            "authority_epoch": self.authority_epoch,
        }

    def effect(self, commit: dict, request: dict) -> None:
        if digest(request) != commit["request_digest"]:
            raise PermissionError("EXECUTION_BINDING_VIOLATION")


def test_t05_a_allow_prepare_commit_effect():
    b = Boundary()
    request = {"tool": "move", "args": {"destination": "cell-3"}}
    p = b.prepare(request)
    c = b.commit(p)
    b.effect(c, request)


def test_t05_b_stale_authority_refuses_commit():
    b = Boundary()
    p = b.prepare({"tool": "move", "args": {"destination": "cell-3"}})
    b.authority_epoch = 2
    with pytest.raises(PermissionError, match="STALE_AUTHORITY_EPOCH"):
        b.commit(p)


def test_t05_c_request_substitution_refuses_commit():
    b = Boundary()
    p = b.prepare({"tool": "move", "args": {"destination": "cell-3"}})
    with pytest.raises(PermissionError, match="REQUEST_SUBSTITUTION"):
        b.commit(p, {"tool": "move", "args": {"destination": "cell-9"}})


def test_t05_d_execution_substitution_refuses_effect():
    b = Boundary()
    request = {"tool": "move", "args": {"destination": "cell-3"}}
    c = b.commit(b.prepare(request))
    with pytest.raises(PermissionError, match="EXECUTION_BINDING_VIOLATION"):
        b.effect(c, {"tool": "move", "args": {"destination": "cell-9"}})
