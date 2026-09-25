"""T32 execution-boundary exclusivity against the real CMCPProxy forwarding seam."""
import asyncio
import json
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import action_binding_digest, request_digest
from tests.test_t30_3_runtime_experiment import _make_proxy, _sink_server


def make_commit(proxy, execution_id, call_id, args, commit_id):
    tool = "test.effect"
    policy = "t32-policy"
    digest = request_digest(tool, args)
    return EABCCommit(
        commit_id=commit_id,
        agent_identity=proxy._session.session_id,
        execution_id=execution_id,
        call_id=call_id,
        tool_name=tool,
        request_payload_hash=digest,
        policy_id=policy,
        action_binding=action_binding_digest(
            agent_identity=proxy._session.session_id,
            execution_id=execution_id,
            tool_name=tool,
            request_payload_hash=digest,
            policy_id=policy,
        ),
        authority_ref="authority-t32",
    )


async def invoke(proxy, call_id, args, execution_id=None):
    with patch.object(proxy, "_check_health", return_value=None):
        return await proxy.call_tool(call_id, "test.effect", args, execution_id=execution_id)


def instrument(proxy, counters):
    original = proxy._forward_to_upstream
    async def wrapped(*args, **kwargs):
        counters["forwarding_entry_count"] += 1
        return await original(*args, **kwargs)
    proxy._forward_to_upstream = wrapped


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["OPTIONAL", "MANDATORY"])
async def test_t32_a_valid_commit(mode, tmp_path: Path):
    sink = tmp_path / "a.jsonl"
    server, url = _sink_server(sink)
    try:
        proxy = _make_proxy(url)
        proxy._t32_mode = mode
        execution_id, call_id, args = "exec-a-" + mode, "call-a-" + mode, {"value": 1}
        proxy._t30_3_adapter = EABCMCPAdapter()
        proxy._t30_3_commit = make_commit(proxy, execution_id, call_id, args, "commit-a-" + mode)
        proxy._t30_3_policy_id = "t32-policy"
        counters = {"forwarding_entry_count": 0}
        instrument(proxy, counters)
        result = await invoke(proxy, call_id, args, execution_id)
        assert result.allowed is True
        assert counters["forwarding_entry_count"] == 1
        assert len(sink.read_text().splitlines()) == 1
    finally:
        server.shutdown()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["OPTIONAL", "MANDATORY"])
async def test_t32_b_no_commit_never_reaches_forwarding(mode, tmp_path: Path):
    sink = tmp_path / "b.jsonl"
    server, url = _sink_server(sink)
    try:
        proxy = _make_proxy(url)
        proxy._t32_mode = mode
        proxy._t30_3_adapter = EABCMCPAdapter()
        counters = {"forwarding_entry_count": 0}
        instrument(proxy, counters)
        with pytest.raises(PermissionError, match="EABC_NO_COMMIT"):
            await invoke(proxy, "call-b", {"value": 2}, "exec-b")
        assert counters["forwarding_entry_count"] == 0
        assert not sink.exists() or not sink.read_text()
    finally:
        server.shutdown()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["OPTIONAL", "MANDATORY"])
async def test_t32_c_substitution_never_reaches_forwarding(mode, tmp_path: Path):
    sink = tmp_path / "c.jsonl"
    server, url = _sink_server(sink)
    try:
        proxy = _make_proxy(url)
        proxy._t32_mode = mode
        execution_id, call_id = "exec-c-" + mode, "call-c-" + mode
        committed = {"value": 3}
        supplied = {"value": 4}
        proxy._t30_3_adapter = EABCMCPAdapter()
        proxy._t30_3_commit = make_commit(proxy, execution_id, call_id, committed, "commit-c-" + mode)
        proxy._t30_3_policy_id = "t32-policy"
        counters = {"forwarding_entry_count": 0}
        instrument(proxy, counters)
        with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
            await invoke(proxy, call_id, supplied, execution_id)
        assert counters["forwarding_entry_count"] == 0
        assert not sink.exists() or not sink.read_text()
    finally:
        server.shutdown()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode, expected", [("OPTIONAL", True), ("MANDATORY", False)])
async def test_t32_d_non_correlated_follows_selected_profile(mode, expected, tmp_path: Path):
    sink = tmp_path / "d.jsonl"
    server, url = _sink_server(sink)
    try:
        proxy = _make_proxy(url)
        proxy._t32_mode = mode
        counters = {"forwarding_entry_count": 0}
        instrument(proxy, counters)
        if expected:
            result = await invoke(proxy, "call-d", {"value": 5})
            assert result.allowed is True
        else:
            with pytest.raises(PermissionError, match="EABC_EXECUTION_ADMISSION_REQUIRED"):
                await invoke(proxy, "call-d", {"value": 5})
        assert counters["forwarding_entry_count"] == int(expected)
        assert (len(sink.read_text().splitlines()) if sink.exists() else 0) == int(expected)
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_t32_replay_has_one_forwarding(tmp_path: Path):
    sink = tmp_path / "replay.jsonl"
    server, url = _sink_server(sink)
    try:
        proxy = _make_proxy(url)
        proxy._t32_mode = "MANDATORY"
        execution_id, call_id, args = "exec-replay", "call-replay", {"value": 6}
        proxy._t30_3_adapter = EABCMCPAdapter()
        proxy._t30_3_commit = make_commit(proxy, execution_id, call_id, args, "commit-replay")
        proxy._t30_3_policy_id = "t32-policy"
        counters = {"forwarding_entry_count": 0}
        instrument(proxy, counters)
        await invoke(proxy, call_id, args, execution_id)
        with pytest.raises(PermissionError, match="EABC_COMMIT_REPLAY"):
            await invoke(proxy, call_id, args, execution_id)
        assert counters["forwarding_entry_count"] == 1
        assert len(sink.read_text().splitlines()) == 1
    finally:
        server.shutdown()


def test_t32_concurrent_same_execution_id_allows_at_most_one_forwarding(tmp_path: Path):
    sink = tmp_path / "race.jsonl"
    server, url = _sink_server(sink)
    try:
        execution_id = "exec-race"
        args = {"value": 7}
        barrier = threading.Barrier(2)
        results = [None, None]

        def worker(i):
            async def run():
                proxy = _make_proxy(url)
                proxy._t32_mode = "MANDATORY"
                proxy._t30_3_adapter = EABCMCPAdapter()
                proxy._t30_3_commit = make_commit(proxy, execution_id, "call-race-" + str(i), args, "commit-race-" + str(i))
                proxy._t30_3_policy_id = "t32-policy"
                counters = {"forwarding_entry_count": 0}
                proxy._t30_3_before_forward = lambda: barrier.wait(timeout=10)
                instrument(proxy, counters)
                try:
                    await invoke(proxy, "call-race-" + str(i), args, execution_id)
                    return counters["forwarding_entry_count"], True
                except PermissionError:
                    return counters["forwarding_entry_count"], False
            results[i] = asyncio.run(run())

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=15)
        assert all(not t.is_alive() for t in threads)
        assert sum(r[0] for r in results) == 1
        assert sum(r[1] for r in results) == 1
        assert len(sink.read_text().splitlines()) == 1
    finally:
        server.shutdown()
