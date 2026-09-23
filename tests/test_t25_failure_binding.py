"""T25.4 — verify EABC-relevant failure semantics against cMCP finalization states."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.session.state import SessionState
from cmcp_runtime.mcp.proxy import _EffectBoundaryState


def make_proxy():
    from cmcp_runtime.mcp.proxy import CMCPProxy

    entry = CatalogEntry(
        tool_name="test.echo",
        server=ServerIdentity(
            display_name="T25.4 Mock",
            url="https://local.invalid/mcp",
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
        added_at="2026-09-23T00:00:00Z",
        approved_by="t25.4",
    )
    catalog = ToolCatalog(entries={"test.echo": entry}, catalog_hash="sha256:" + "1" * 64)
    config = Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch(
        "cmcp_runtime.mcp.proxy.MCPResponseScanner"
    ):
        proxy = CMCPProxy(
            catalog=catalog,
            policy_evaluator=MagicMock(),
            session=SessionState(session_id="t25.4"),
            audit_chain=AuditChain("t25.4"),
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
async def test_commit_then_transport_failure_is_outcome_unknown():
    proxy = make_proxy()

    async def forward(*args, **kwargs):
        finalization = kwargs["finalization"]
        finalization.eabc_commit_id = "eabc-t25.4-unknown"
        finalization.effect_boundary_state = _EffectBoundaryState.TRANSPORT_MAY_HAVE_STARTED
        raise RuntimeError("transport-ambiguous")

    proxy._forward_to_upstream = forward

    with pytest.raises(RuntimeError, match="transport-ambiguous"):
        await proxy.call_tool("t25.4-unknown", "test.echo", {"x": 1})

    terminal = proxy._audit.entries[-1]
    assert terminal.entry_type == "fault"
    assert terminal.detail["effect_boundary_state"] == "transport_may_have_started"
    assert terminal.detail["terminal_disposition"] == "outcome_unknown"


@pytest.mark.asyncio
async def test_commit_then_pre_transport_failure_is_not_attempted():
    proxy = make_proxy()

    async def forward(*args, **kwargs):
        finalization = kwargs["finalization"]
        finalization.eabc_commit_id = "eabc-t25.4-pre"
        assert finalization.effect_boundary_state == _EffectBoundaryState.PRE_TRANSPORT
        raise RuntimeError("pre-transport")

    proxy._forward_to_upstream = forward

    with pytest.raises(RuntimeError, match="pre-transport"):
        await proxy.call_tool("t25.4-pre", "test.echo", {"x": 1})

    terminal = proxy._audit.entries[-1]
    assert terminal.detail["effect_boundary_state"] == "pre_transport"
    assert terminal.detail["terminal_disposition"] == "not_attempted"


@pytest.mark.asyncio
async def test_cancellation_after_transport_started_is_outcome_unknown():
    proxy = make_proxy()
    started = asyncio.Event()

    async def forward(*args, **kwargs):
        kwargs["finalization"].eabc_commit_id = "eabc-t25.4-cancel"
        kwargs["finalization"].effect_boundary_state = _EffectBoundaryState.TRANSPORT_MAY_HAVE_STARTED
        started.set()
        await asyncio.Future()

    proxy._forward_to_upstream = forward
    task = asyncio.create_task(proxy.call_tool("t25.4-cancel", "test.echo", {"x": 1}))
    await started.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    terminal = proxy._audit.entries[-1]
    assert terminal.detail["effect_boundary_state"] == "transport_may_have_started"
    assert terminal.detail["terminal_disposition"] == "outcome_unknown"
