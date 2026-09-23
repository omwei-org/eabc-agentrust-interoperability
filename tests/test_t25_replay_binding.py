"""T25.5 — replay/duplicate execution after an EABC COMMIT."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.mcp.proxy import CMCPProxy


def make_proxy():
    entry = CatalogEntry(
        tool_name="test.echo",
        server=ServerIdentity(
            display_name="T25.5 Mock",
            url="https://local.invalid/mcp",
            tls_fingerprint="SHA256:" + "A" * 43 + "=",
            spiffe_id=None, transport="http-sse", rotation_mode="key-pinned",
        ),
        approved_definition=ApprovedDefinition(
            description="echo", input_schema={"type": "object"}, output_schema=None
        ),
        definition_hash="sha256:" + "0" * 64,
        compliance_domain="public", requires_baa=False, sensitivity_level="public",
        added_at="2026-09-23T00:00:00Z", approved_by="t25.5",
    )
    catalog = ToolCatalog(entries={"test.echo": entry}, catalog_hash="sha256:" + "1" * 64)
    config = Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        proxy = CMCPProxy(
            catalog=catalog, policy_evaluator=MagicMock(),
            session=__import__("cmcp_runtime.session.state", fromlist=["SessionState"]).SessionState(session_id="t25.5"),
            audit_chain=AuditChain("t25.5"), config=config,
        )
    proxy._check_health = MagicMock(return_value=None)
    proxy._check_upstream_drift = AsyncMock(return_value=False)
    proxy._policy.evaluate.return_value = MagicMock(rule_matched="test.allow", would_have_denied=False, advice={})
    proxy._mcp_gateway.intercept_tool_call.return_value = (True, "")
    proxy._mcp_gateway.intercept_tool_response.return_value = MagicMock(threats=[], content=None, allowed=True)
    proxy._policy.authorize_egress.return_value = MagicMock(would_have_denied=False, advice={})
    return proxy


@pytest.mark.asyncio
async def test_same_commit_cannot_be_forwarded_twice():
    proxy = make_proxy()
    seen = set()
    effects = []

    async def forward(call_id, entry, tool_name, arguments, *, finalization=None):
        commit_id = getattr(finalization, "eabc_commit_id", None)
        assert commit_id is not None
        if commit_id in seen:
            raise PermissionError("EABC_COMMIT_REPLAY")
        seen.add(commit_id)
        effects.append((commit_id, call_id, tool_name, arguments))
        finalization.effect_boundary_state = __import__(
            "cmcp_runtime.mcp.proxy", fromlist=["_EffectBoundaryState"]
        )._EffectBoundaryState.TRANSPORT_RESPONSE_RECEIVED
        return {"content": [{"type": "text", "text": "ok"}]}

    proxy._forward_to_upstream = forward

    # Two distinct cMCP calls attempt to reuse the same EABC commit.
    for call_id in ("t25.5-a", "t25.5-b"):
        finalization_commit = "eabc-t25.5-replay"
        original = proxy._forward_to_upstream
        async def gated(call_id_, entry_, tool_name_, arguments_, *, finalization=None):
            finalization.eabc_commit_id = finalization_commit
            return await original(call_id_, entry_, tool_name_, arguments_, finalization=finalization)
        proxy._forward_to_upstream = gated
        if call_id.endswith("a"):
            await proxy.call_tool(call_id, "test.echo", {"x": 1})
        else:
            with pytest.raises(PermissionError, match="EABC_COMMIT_REPLAY"):
                await proxy.call_tool(call_id, "test.echo", {"x": 1})

    assert len(effects) == 1
    assert proxy._audit.verify_chain() is True
