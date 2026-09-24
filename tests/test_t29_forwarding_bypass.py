"""T29 — forwarding-boundary bypass experiment.

This test deliberately distinguishes two claims:
1. the EABC adapter can gate the public CMCPProxy.call_tool() path;
2. the underlying cMCP forwarding primitive remains callable directly in the
   test process, which is not a cMCP vulnerability claim because _forward_to_upstream
   is an internal method and the test bypasses the public gateway entrypoint.
"""
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
            display_name="T29 Mock",
            url="http://127.0.0.1:9/mcp",
            tls_fingerprint="SHA256:" + "A" * 43 + "=",
            spiffe_id=None,
            transport="http-sse",
            rotation_mode="key-pinned",
        ),
        approved_definition=ApprovedDefinition(
            description="echo", input_schema={"type": "object"}, output_schema=None
        ),
        definition_hash="sha256:" + "0" * 64,
        compliance_domain="public",
        requires_baa=False,
        sensitivity_level="public",
        added_at="2026-09-24T00:00:00Z",
        approved_by="t29",
    )
    catalog = ToolCatalog(
        entries={"test.echo": entry}, catalog_hash="sha256:" + "1" * 64
    )
    config = Config(
        attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING)
    )
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch(
        "cmcp_runtime.mcp.proxy.MCPResponseScanner"
    ):
        proxy = CMCPProxy(
            catalog=catalog,
            policy_evaluator=MagicMock(),
            session=SessionState(session_id="t29"),
            audit_chain=AuditChain("t29"),
            config=config,
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
async def test_t29_public_path_without_commit_is_blocked():
    proxy = make_proxy()
    adapter = EABCMCPAdapter()
    effects = []

    original = proxy._forward_to_upstream

    async def gated_forward(call_id, entry, tool_name, arguments, **kwargs):
        commit = getattr(proxy, "_t29_commit", None)
        if commit is None:
            raise PermissionError("EABC_NO_COMMIT")
        adapter.validate(
            commit,
            call_id=call_id,
            tool_name=tool_name,
            arguments=arguments,
            policy_id="policy-A",
        )
        effects.append((call_id, tool_name, arguments.copy()))
        return await original(call_id, entry, tool_name, arguments, **kwargs)

    proxy._forward_to_upstream = gated_forward

    with pytest.raises(PermissionError, match="EABC_NO_COMMIT"):
        await proxy.call_tool("t29-public-001", "test.echo", {"x": 1})

    assert effects == []


@pytest.mark.asyncio
async def test_t29_direct_internal_forwarding_can_bypass_adapter_gate():
    proxy = make_proxy()
    effects = []

    async def direct_effect(call_id, entry, tool_name, arguments, **kwargs):
        effects.append((call_id, tool_name, arguments.copy()))
        return "direct-effect"

    # The test replaces the cMCP transport operation itself. It intentionally
    # calls the internal forwarding method, not the public call_tool path.
    proxy._forward_to_upstream = direct_effect

    await proxy._forward_to_upstream(
        "t29-direct-001",
        proxy._catalog.lookup("test.echo"),
        "test.echo",
        {"x": 1},
    )

    assert effects == [("t29-direct-001", "test.echo", {"x": 1})]


@pytest.mark.asyncio
async def test_t29_valid_commit_allows_only_matching_public_execution():
    proxy = make_proxy()
    adapter = EABCMCPAdapter()
    effects = []

    async def gated_effect(call_id, entry, tool_name, arguments, **kwargs):
        commit = getattr(proxy, "_t29_commit", None)
        if commit is None:
            raise PermissionError("EABC_NO_COMMIT")
        adapter.validate(
            commit,
            call_id=call_id,
            tool_name=tool_name,
            arguments=arguments,
            policy_id="policy-A",
        )
        effects.append((call_id, tool_name, arguments.copy()))
        return "ok"

    proxy._forward_to_upstream = gated_effect
    args = {"x": 1}
    proxy._t29_commit = EABCCommit(
        commit_id="t29-commit-001",
        call_id="t29-public-002",
        tool_name="test.echo",
        request_payload_hash=request_digest("test.echo", args),
        policy_id="policy-A",
    )

    result = await proxy.call_tool("t29-public-002", "test.echo", args)

    assert result.allowed is True
    assert effects == [("t29-public-002", "test.echo", args)]
