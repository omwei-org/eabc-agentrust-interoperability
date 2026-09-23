from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


def canonical_args(args: dict) -> bytes:
    return json.dumps(args, sort_keys=True, separators=(",", ":")).encode()


def request_digest(args: dict) -> str:
    return "sha256:" + hashlib.sha256(canonical_args(args)).hexdigest()


@dataclass(frozen=True)
class CommitEnvelope:
    commit_id: str
    execution_id: str
    request_payload_hash: str
    policy_bundle_hash: str
    authority_epoch: int
    tool_name: str


class CommitAdapter:
    def __init__(self, policy_hash: str = "sha256:H1", authority_epoch: int = 1):
        self.policy_hash = policy_hash
        self.authority_epoch = authority_epoch
        self._counter = 0

    def prepare(self, execution_id: str, tool_name: str, args: dict) -> dict:
        return {
            "execution_id": execution_id,
            "tool_name": tool_name,
            "arguments": args,
            "request_payload_hash": request_digest(args),
            "policy_bundle_hash": self.policy_hash,
            "authority_epoch": self.authority_epoch,
        }

    def commit(self, prepared: dict) -> CommitEnvelope:
        if prepared["authority_epoch"] != self.authority_epoch:
            raise PermissionError("STALE_AUTHORITY")
        if prepared["policy_bundle_hash"] != self.policy_hash:
            raise PermissionError("STALE_POLICY")
        if request_digest(prepared["arguments"]) != prepared["request_payload_hash"]:
            raise PermissionError("REQUEST_BINDING_MISMATCH")
        self._counter += 1
        return CommitEnvelope(
            commit_id=f"commit-{self._counter}",
            execution_id=prepared["execution_id"],
            request_payload_hash=prepared["request_payload_hash"],
            policy_bundle_hash=prepared["policy_bundle_hash"],
            authority_epoch=self.authority_epoch,
            tool_name=prepared["tool_name"],
        )

    def effect(self, commit: CommitEnvelope, execution_id: str, tool_name: str, args: dict) -> None:
        if execution_id != commit.execution_id:
            raise PermissionError("EXECUTION_ID_MISMATCH")
        if tool_name != commit.tool_name:
            raise PermissionError("TOOL_MISMATCH")
        if request_digest(args) != commit.request_payload_hash:
            raise PermissionError("REQUEST_DIGEST_MISMATCH")


def test_t14_valid_commit_reaches_exact_effect():
    a = CommitAdapter()
    args = {"destination": "cell-3", "speed": 1}
    p = a.prepare("exec-001", "move", args)
    c = a.commit(p)
    a.effect(c, "exec-001", "move", args)


def test_t14_no_commit_no_effect():
    a = CommitAdapter()
    args = {"destination": "cell-3"}
    p = a.prepare("exec-002", "move", args)
    try:
        a.effect(None, "exec-002", "move", args)
        assert False
    except AttributeError:
        pass


def test_t14_wrong_request_digest_no_effect():
    a = CommitAdapter()
    p = a.prepare("exec-003", "move", {"destination": "cell-3"})
    c = a.commit(p)
    try:
        a.effect(c, "exec-003", "move", {"destination": "cell-9"})
        assert False
    except PermissionError as e:
        assert str(e) == "REQUEST_DIGEST_MISMATCH"


def test_t14_stale_authority_no_commit():
    a = CommitAdapter()
    p = a.prepare("exec-004", "move", {"destination": "cell-3"})
    a.authority_epoch = 2
    try:
        a.commit(p)
        assert False
    except PermissionError as e:
        assert str(e) == "STALE_AUTHORITY"


def test_t14_stale_policy_no_commit():
    a = CommitAdapter()
    p = a.prepare("exec-005", "move", {"destination": "cell-3"})
    a.policy_hash = "sha256:H2"
    try:
        a.commit(p)
        assert False
    except PermissionError as e:
        assert str(e) == "STALE_POLICY"
