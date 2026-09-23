"""T25.3 — bind an EABC commit to cMCP finalization and terminal evidence."""

from __future__ import annotations

import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.session.state import SessionState


def digest(arguments):
    payload = json.dumps(arguments, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def make_proxy():
    from cmcp_runtime.mcp.proxy import CMCPProxy

    server = ServerIdentity(
        display_name="T25 Mock",
        url="http://127.0.0.1:9/mcp",
        tls_fingerprint="SHA256:" + "A" * 43 + "=",
        spiffe_id=None,
        transport="http-sse",
        rotation_mode="key-pinned",
    )
    entry = CatalogEntry(
        tool_name="test.echo",
        server=server,
        approved_definition=ApprovedDefinition(
            description="echo",
            input_schema={"type": "object"},
            output_schema=None,
        ),
        definition_hash="sha256:" + "0" * 64,
        compliance_domain="public",
        requires_baa=False,
        sensitivity_level="public",
        added_at="2026-06-10T00:00:00Z",
        approved_by="test",
    )
    catalog = ToolCatalog(entries={"test.echo": entry}, catalog_hash="sha256:" + "1" * 64)
    config = Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    session = SessionState(session_id="t25")
    chain = AuditChain("t25")

    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch(
        "cmcp_runtime.mcp.proxy.MCPResponseScanner"
    ):
        proxy = CMCPProxy(
            catalog=catalog,
            policy_evaluator=MagicMock(),
            session=session,
            audit_chain=chain,
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
async def test_t25_commit_tuple_is_reconstructable_from_terminal_audit():
    proxy = make_proxy()
    call_id = "t25-call-103"
    args = {"message": "hello", "n": 1}
    request_hash = digest(args)

    async def gated_forward(call_id, entry, tool_name, arguments, *, finalization=None):
        assert finalization is not None
        assert finalization.request_payload_hash == request_hash
        return json.dumps({"ok": True})

    proxy._forward_to_upstream = gated_forward
    result = await proxy.call_tool(call_id, "test.echo", args)

    terminal = proxy._audit.entries[-1]
    assert terminal.call_id == call_id
    assert terminal.tool_name == "test.echo"
    assert terminal.request_payload_hash == request_hash
    assert result.audit_entry_hash == terminal.entry_hash
    assert proxy._audit.verify_chain() is True


@pytest.mark.asyncio
async def test_t25_commit_id_is_not_present_in_production_terminal_audit():
    proxy = make_proxy()
    call_id = "t25-call-104"
    args = {"message": "hello"}

    async def gated_forward(call_id, entry, tool_name, arguments, *, finalization=None):
        assert finalization is not None
        finalization.eabc_commit_id = "eabc-t25-104"
        return json.dumps({"ok": True})

    proxy._forward_to_upstream = gated_forward
    result = await proxy.call_tool(call_id, "test.echo", args)

    terminal = proxy._audit.entries[-1]
    serialized = terminal._canonical_body().decode()

    assert "eabc-t25-104" not in serialized
    assert result.audit_entry_hash == terminal.entry_hash


@pytest.mark.asyncio
async def test_t25_commit_binding_fails_closed_before_upstream_effect():
    proxy = make_proxy()

    async def gated_forward(call_id, entry, tool_name, arguments, *, finalization=None):
        assert finalization is not None
        raise PermissionError("EABC_COMMIT_REQUIRED")

    proxy._forward_to_upstream = gated_forward

    with pytest.raises(PermissionError, match="EABC_COMMIT_REQUIRED"):
        await proxy.call_tool("t25-call-105", "test.echo", {"message": "hello"})
