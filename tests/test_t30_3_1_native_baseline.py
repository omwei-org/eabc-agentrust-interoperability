"""Native pinned cMCP baseline for T30.3.1."""

from pathlib import Path

import pytest

from tests.test_t30_3_runtime_experiment import _make_proxy, _sink_server


@pytest.mark.asyncio
async def test_native_valid_execution_id_is_fail_closed_before_upstream(tmp_path: Path):
    sink = tmp_path / "native-baseline.jsonl"
    server, url = _sink_server(sink)
    try:
        proxy = _make_proxy(url)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(proxy, "_check_health", lambda: None)
            result = await proxy.call_tool(
                "native-baseline-call",
                "test.effect",
                {"destination": "native-baseline", "value": 0},
                execution_id="native-baseline-execution",
            )
        assert result.allowed is False
        assert not sink.exists() or sink.read_text() == ""
    finally:
        server.shutdown()
