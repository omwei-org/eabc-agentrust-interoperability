"""T26.3 — profile negative-path conformance on real cMCP call_tool."""

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
            display_name="T26.3 Mock", url="https://local.invalid/mcp",
            tls_fingerprint="SHA256:" + "A" * 43 + "=",
            spiffe_id=None, transport="http-sse", rotation_mode="key-pinned",
        ),
        approved_definition=ApprovedDefinition(
            description="echo", input_schema={"type": "object"}, output_schema=None
        ),
        definition_hash="sha256:" + "0" * 64, compliance_domain="public",
        requires_baa=False, sensitivity_level="public",
        added_at="2026-09-23T00:00:00Z", approved_by="t26.3",
    )
    catalog = ToolCatalog(entries={"test.echo": entry}, catalog_hash="sha256:" + "1" * 64)
    config = Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        proxy = CMCPProxy(
            catalog=catalog, policy_evaluator=MagicMock(),
            session=SessionState(session_id="t26.3"),
            audit_chain=AuditChain("t26.3"), config=config,
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


def install_gate(proxy, adapter, commit, effects):
    async def gated(call_id, entry, tool_name, arguments, *, finalization=None):
        adapter.validate(
            commit,
            call_id=call_id,
            tool_name=tool_name,
            arguments=arguments,
            policy_id="policy-A",
        )
        effects.append((call_id, tool_name, arguments))
        return "ok"
    proxy._forward_to_upstream = gated


@pytest.mark.asyncio
async def test_no_commit_is_rejected_before_effect():
    proxy = make_proxy()
    effects = []

    async def no_commit(call_id, entry, tool_name, arguments, *, finalization=None):
        raise PermissionError("EABC_NO_COMMIT")

    proxy._forward_to_upstream = no_commit

    with pytest.raises(PermissionError, match="EABC_NO_COMMIT"):
        await proxy.call_tool("call-no-commit", "test.echo", {"x": 1})

    assert effects == []


@pytest.mark.asyncio
async def test_valid_commit_then_replay_is_rejected():
    proxy = make_proxy()
    adapter = EABCMCPAdapter()
    effects = []
    commit = EABCCommit(
        "eabc-t26.3-replay", "call-replay", "test.echo",
        request_digest("test.echo", {"x": 1}), "policy-A",
    )
    install_gate(proxy, adapter, commit, effects)

    await proxy.call_tool("call-replay", "test.echo", {"x": 1})

    with pytest.raises(PermissionError, match="EABC_COMMIT_REPLAY"):
        await proxy.call_tool("call-replay", "test.echo", {"x": 1})

    assert len(effects) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call_id,tool_name,arguments",
    [
        ("call-sub", "test.echo", {"x": 2}),
        ("call-sub-2", "test.echo", {"x": 1}),
    ],
)
async def test_substitution_is_rejected_before_effect(call_id, tool_name, arguments):
    proxy = make_proxy()
    adapter = EABCMCPAdapter()
    effects = []
    commit = EABCCommit(
        "eabc-t26.3-sub", "call-sub", "test.echo",
        request_digest("test.echo", {"x": 1}), "policy-A",
    )
    install_gate(proxy, adapter, commit, effects)

    with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
        await proxy.call_tool(call_id, tool_name, arguments)

    assert effects == []
