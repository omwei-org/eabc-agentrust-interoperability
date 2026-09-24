"""T30.3.1: differential TOCTOU and concurrency experiment."""

from __future__ import annotations

import asyncio
import hashlib
import json
import threading
from pathlib import Path

import pytest

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import action_binding_digest, request_digest
from tests.test_t30_3_runtime_experiment import _make_proxy, _sink_server


def _commit(execution_id: str, call_id: str, args: dict, commit_id: str = 'commit-t30-3-1') -> EABCCommit:
    agent = "t30-3-1-agent"
    tool = "test.effect"
    policy = "t30.3.1-policy"
    request_hash = request_digest(tool, args)
    return EABCCommit(
        commit_id=commit_id,
        agent_identity=agent,
        execution_id=execution_id,
        call_id=call_id,
        tool_name=tool,
        request_payload_hash=request_hash,
        policy_id=policy,
        action_binding=action_binding_digest(
            agent_identity=agent,
            execution_id=execution_id,
            tool_name=tool,
            request_payload_hash=request_hash,
            policy_id=policy,
        ),
        authority_ref="authority-t30-3-1",
    )


@pytest.mark.asyncio
async def test_t30_3_1_revocation_between_admission_and_forwarding(tmp_path: Path):
    sink = tmp_path / "revocation.jsonl"
    server, url = _sink_server(sink)
    try:
        proxy = _make_proxy(url)
        execution_id = "exec-t30-3-1-revoke"
        args = {"destination": "revoke", "value": 1}
        proxy._t30_3_adapter = EABCMCPAdapter()
        proxy._t30_3_commit = _commit(execution_id, "call-revoke", args)
        proxy._t30_3_policy_id = "t30.3.1-policy"
        authority = {"valid": True}

        def invalidate():
            authority["valid"] = False

        def final_check():
            if not authority["valid"]:
                raise PermissionError("EABC_AUTHORITY_REVOKED")

        proxy._t30_3_before_forward = invalidate
        proxy._t30_3_final_authority_check = final_check

        with pytest.raises(PermissionError, match="EABC_AUTHORITY_REVOKED"):
            with __import__("unittest").mock.patch.object(proxy, "_check_health", return_value=None):
                await proxy.call_tool("call-revoke", "test.effect", args, execution_id=execution_id)

        assert not sink.exists() or sink.read_text() == ""
    finally:
        server.shutdown()


def test_t30_3_1_concurrent_same_execution_id_allows_at_most_one_effect(tmp_path: Path):
    sink = tmp_path / "concurrent.jsonl"
    server, url = _sink_server(sink)
    try:
        execution_id = "exec-t30-3-1-concurrent"
        args = {"destination": "concurrent", "value": 2}
        commits = [_commit(execution_id, "call-concurrent-1", args, "commit-t30-3-1-a"), _commit(execution_id, "call-concurrent-2", args, "commit-t30-3-1-b")]
        barrier = threading.Barrier(2)

        def before_forward():
            barrier.wait(timeout=10)

        def invoke(commit):
            async def run():
                from unittest.mock import patch
                proxy = _make_proxy(url)
                proxy._session.session_id = "t30-3-1-agent"
                proxy._t30_3_adapter = EABCMCPAdapter()
                proxy._t30_3_commit = commit
                proxy._t30_3_policy_id = "t30.3.1-policy"
                proxy._t30_3_before_forward = before_forward
                proxy._t30_3_final_authority_check = lambda: None
                with patch.object(proxy, "_check_health", return_value=None):
                    try:
                        await proxy.call_tool(
                            commit.call_id, "test.effect", args, execution_id=execution_id
                        )
                        return "effect"
                    except PermissionError as exc:
                        return str(exc)

            return asyncio.run(run())

        results = [None, None]

        def worker(i):
            results[i] = invoke(commits[i])

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        assert all(not t.is_alive() for t in threads)
        assert results.count("effect") == 1
        assert len(sink.read_text().splitlines()) == 1
        assert "EABC_EXECUTION_ALREADY_RESERVED" in results
    finally:
        server.shutdown()


def test_t30_3_1_evidence_record_shape(tmp_path: Path):
    evidence = {
        "experiment": "T30.3.1",
        "upstream_commit": "f8743e013786b094caaa70c336519834e73c74d5",
        "baseline": "native pinned runtime / no repository patch",
        "control": "same runtime with forwarding admission enabled and EABC hook disabled",
        "cases": [
            "valid",
            "revocation_between_admission_and_forward",
            "argument_substitution",
            "replay",
            "concurrent_same_execution_id",
        ],
        "observable": {"sink_sha256": hashlib.sha256(b"").hexdigest()},
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    assert json.loads(path.read_text())["experiment"] == "T30.3.1"
