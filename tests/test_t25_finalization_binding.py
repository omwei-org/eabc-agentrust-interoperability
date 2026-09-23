"""T25.3 — bind an EABC commit to cMCP's existing finalization and terminal evidence."""

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
async def test_t25_commit_binds_to_existing_finalization_and_terminal_audit():
    proxy = make_proxy()
    call_id = "t25-call-101"
    args = {"message": "hello", "n": 1}
    commit = {
        "commit_id": "eabc-t25-101",
        "call_id": call_id,
        "tool_name": "test.echo",
        "request_payload_hash": digest(args),
    }
    observed = {}

    async def gated_forward(call_id, entry, tool_name, arguments, *, finalization=None):
        assert finalization is not None
        assert finalization.request_payload_hash == digest(arguments)

        # Bind the EABC commit to the SAME cMCP finalization object that
        # call_tool() will later use for terminal persistence.
        finalization.eabc_commit_id = commit["commit_id"]
        finalization.eabc_commit_call_id = call_id

        observed["forward"] = {
            "call_id": call_id,
            "commit_id": finalization.eabc_commit_id,
            "request_payload_hash": finalization.request_payload_hash,
        }
        return json.dumps({"ok": True})

    proxy._forward_to_upstream = gated_forward
    result = await proxy.call_tool(call_id, "test.echo", args)

    assert result.allowed is True
    assert observed["forward"]["commit_id"] == commit["commit_id"]
    assert observed["forward"]["call_id"] == call_id
    assert observed["forward"]["request_payload_hash"] == digest(args)
    assert result.audit_entry_hash == proxy._audit.chain_tip

    # T25.3 discovery: the upstream _CallFinalizationState currently has no
    # normative EABC commit field. The experiment can attach one dynamically,
    # but cMCP's production terminal audit does not serialize it today.
    # Therefore this test demonstrates object-level binding, not production
    # EABC evidence binding.
    assert getattr(proxy, "_audit").chain_tip


@pytest.mark.asyncio
async def test_t25_commit_binding_fails_closed_before_upstream_effect():
    proxy = make_proxy()
    call_id = "t25-call-102"
    args = {"message": "hello"}

    async def gated_forward(call_id, entry, tool_name, arguments, *, finalization=None):
        if finalization is None:
            raise AssertionError("missing finalization")
        raise PermissionError("EABC_COMMIT_REQUIRED")

    proxy._forward_to_upstream = gated_forward

    with pytest.raises(PermissionError, match="EABC_COMMIT_REQUIRED"):
        await proxy.call_tool(call_id, "test.echo", args)
