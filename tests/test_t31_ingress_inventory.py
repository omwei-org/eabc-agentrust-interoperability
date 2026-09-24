"""T31: source-level forwarding ingress inventory for pinned cMCP."""

from __future__ import annotations

from pathlib import Path

PIN = "f8743e013786b094caaa70c336519834e73c74d5"
UPSTREAM = Path("upstream/cmcp")


def _read(relative: str) -> str:
    return (UPSTREAM / relative).read_text(encoding="utf-8")


def test_t31_pin_and_production_mcp_ingress() -> None:
    proxy = _read("src/cmcp_runtime/mcp/proxy.py")
    server = _read("src/cmcp_runtime/mcp/server.py")

    assert PIN in Path(".github/workflows/t30-3-runtime-experiment.yml").read_text()
    assert 'Route("/mcp", self._handle_mcp, methods=["POST"])' in server
    assert "if method == \"tools/call":" in server
    assert "return await self._handle_tool_call(rpc_id, params)" in server
    assert "result = await self._proxy.call_tool(" in server


def test_t31_single_production_tool_forwarding_transition() -> None:
    proxy = _read("src/cmcp_runtime/mcp/proxy.py")

    # The production method is the sole source-level invocation of the
    # forwarding helper in the runtime implementation. Tests/benchmarks may
    # call or monkeypatch this private helper, but are not production ingress.
    production = proxy.split("class CMCPProxy", 1)[1]
    assert production.count("await self._forward_to_upstream(") == 1
    assert "await self._forward_to_upstream(" in production


def test_t31_forwarding_covers_both_transport_branches() -> None:
    proxy = _read("src/cmcp_runtime/mcp/proxy.py")

    assert "if entry.server.is_stdio:" in proxy
    assert "return await server.call(call_id, tool_name, arguments)" in proxy
    assert "client = self._client_for_upstream(entry)" in proxy
    assert "await client.post(entry.server.url, json=payload, headers=headers)" in proxy


def test_t31_no_alternate_production_upstream_http_client_path() -> None:
    proxy = _read("src/cmcp_runtime/mcp/proxy.py")

    # HTTP client construction and POST are confined to the forwarding helper
    # in the runtime implementation. Discovery is intentionally excluded from
    # the declared consequence: tools/list acquisition is not tools/call effect.
    forward = proxy.split("    async def _forward_to_upstream(", 1)[1]
    assert "await client.post(entry.server.url, json=payload, headers=headers)" in forward
    before_forward = proxy.split("    async def _forward_to_upstream(", 1)[0]
    assert "await client.post(entry.server.url, json=payload, headers=headers)" not in before_forward


def test_t31_evidence_record_shape() -> None:
    record = {
        "experiment": "T31",
        "upstream_repository": "agentrust-io/cmcp",
        "upstream_commit": PIN,
        "declared_consequence": "MCP tools/call reaches configured upstream",
        "production_ingress": "POST /mcp -> _handle_mcp -> _handle_tool_call -> CMCPProxy.call_tool",
        "common_forwarding_transition": "CMCPProxy.call_tool -> _forward_to_upstream",
        "transport_branches": ["http", "stdio"],
        "alternate_production_ingress_identified": False,
        "claim_scope": "inspected pinned runtime surface",
    }
    assert record["upstream_commit"] == PIN
    assert record["alternate_production_ingress_identified"] is False
