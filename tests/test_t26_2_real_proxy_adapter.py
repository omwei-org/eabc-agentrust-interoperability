"""T26.2 — reusable EABC-MCP adapter on the real cMCP call_tool path."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.mcp.proxy import CMCPProxy
from cmcp_runtime.session.state import SessionState

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import request_digest


def make_proxy():
    entry = CatalogEntry(
        tool_name="test.echo",
        server=ServerIdentity(
            display_name="T26.2 Mock", url="https://local.invalid/mcp",
            tls_fingerprint="SHA256:" + "A" * 43 + "=",
            spiffe_id=None, transport="http-sse", rotation_mode="key-pinned",
        ),
        approved_definition=ApprovedDefinition(
            description="echo", input_schema={"type": "object"}, output_schema=None
        ),
        definition_hash="sha256:" + "0" * 64, compliance_domain="public",
        requires_baa=False, sensitivity_level="public",
        added_at="2026-09-23T00:00:00Z", approved_by="t26.2",
    )
    catalog = ToolCatalog(entries={"test.echo": entry}, catalog_hash="sha256:" + "1" * 64)
    config = Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        proxy = CMCPProxy(
            catalog=catalog, policy_evaluator=MagicMock(),
            session=SessionState(session_id="t26.2"),
            audit_chain=AuditChain("t26.2"), config=config,
        )
    proxy._check_health = MagicMock(return_value=None)
    proxy._check_upstream_drift = AsyncMock(return_value=False)
    proxy._policy.evaluate.return_value = MagicMock(
        rule_matched="test.allow", would_have_denied=False, advice={}
    )
    proxy._mcp_gateway.intercept_tool_call.return_value = (True, "")
    proxy._mcp_gateway.intercept_tool_response.return_value = MagicMock(
        threats=[], content=None, allowed=True
    )
    proxy._policy.authorize_egress.return_value = MagicMock(
        would_have_denied=False, advice={}
    )
    return proxy


@pytest.mark.asyncio
async def test_real_call_tool_uses_reusable_eabc_adapter_at_forwarding_seam():
    proxy = make_proxy()
    adapter = EABCMCPAdapter()
    effects = []

    commit = EABCCommit(
        commit_id="eabc-t26.2-001",
        call_id="call-001",
        tool_name="test.echo",
        request_payload_hash=request_digest("test.echo", {"x": 1}),
        policy_id="policy-A",
    )

    async def gated_forward(call_id, entry, tool_name, arguments, *, finalization=None):
        adapter.validate(
            commit,
            call_id=call_id,
            tool_name=tool_name,
            arguments=arguments,
            policy_id="policy-A",
        )
        effects.append((call_id, tool_name, arguments))
        return "ok"

    proxy._forward_to_upstream = gated_forward

    result = await proxy.call_tool("call-001", "test.echo", {"x": 1})

    assert result.allowed is True
    assert effects == [("call-001", "test.echo", {"x": 1})]
    assert proxy._audit.verify_chain() is True


@pytest.mark.asyncio
async def test_real_call_tool_rejects_substituted_request_before_forwarding():
    proxy = make_proxy()
    adapter = EABCMCPAdapter()
    effects = []

    commit = EABCCommit(
        commit_id="eabc-t26.2-002",
        call_id="call-002",
        tool_name="test.echo",
        request_payload_hash=request_digest("test.echo", {"x": 1}),
        policy_id="policy-A",
    )

    async def gated_forward(call_id, entry, tool_name, arguments, *, finalization=None):
        adapter.validate(
            commit,
            call_id=call_id,
            tool_name=tool_name,
            arguments=arguments,
            policy_id="policy-A",
        )
        effects.append((call_id, tool_name, arguments))
        return "ok"

    proxy._forward_to_upstream = gated_forward

    with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
        await proxy.call_tool("call-002", "test.echo", {"x": 2})

    assert effects == []
    assert proxy._audit.verify_chain() is True
