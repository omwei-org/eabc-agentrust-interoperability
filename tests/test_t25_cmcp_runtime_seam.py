"""T25.2 — real CMCPProxy.call_tool() with an EABC gate at the existing forwarding seam."""

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
async def test_t25_real_call_tool_valid_commit_reaches_forwarding_and_audit():
    proxy = make_proxy()
    call_id = "t25-call-001"
    args = {"message": "hello", "n": 1}
    commits = {
        call_id: {
            "commit_id": "eabc-t25-call-001",
            "call_id": call_id,
            "tool_name": "test.echo",
            "request_payload_hash": digest(args),
        }
    }
    forwarded = []

    async def eabc_gate(call_id, entry, tool_name, arguments, **kwargs):
        commit = commits.get(call_id)
        assert commit is not None, "EABC commit required before forwarding"
        assert commit["call_id"] == call_id
        assert commit["tool_name"] == tool_name
        assert commit["request_payload_hash"] == digest(arguments)
        forwarded.append(
            {
                "call_id": call_id,
                "tool_name": tool_name,
                "request_payload_hash": digest(arguments),
            }
        )
        return json.dumps({"ok": True})

    # CMCPProxy.call_tool() remains the production implementation.
    # Only its existing forwarding seam is replaced by this disposable gate.
    proxy._forward_to_upstream = eabc_gate

    result = await proxy.call_tool(call_id, "test.echo", args)

    assert result.allowed is True
    assert result.call_id == call_id
    assert forwarded == [{
        "call_id": call_id,
        "tool_name": "test.echo",
        "request_payload_hash": digest(args),
    }]
    assert result.audit_entry_hash == proxy._audit.chain_tip
    assert proxy._audit.chain_tip


@pytest.mark.asyncio
async def test_t25_real_call_tool_without_commit_never_reaches_effect():
    proxy = make_proxy()
    forwarded = []

    async def eabc_gate(call_id, entry, tool_name, arguments, **kwargs):
        raise PermissionError("EABC_NO_COMMIT")

    proxy._forward_to_upstream = eabc_gate

    with pytest.raises(PermissionError, match="EABC_NO_COMMIT"):
        await proxy.call_tool(
            "t25-call-002", "test.echo", {"message": "hello"}
        )

    assert forwarded == []


@pytest.mark.asyncio
async def test_t25_real_call_tool_tampered_arguments_never_reach_effect():
    proxy = make_proxy()
    call_id = "t25-call-003"
    committed_args = {"message": "hello"}
    forwarded = []

    async def eabc_gate(call_id, entry, tool_name, arguments, **kwargs):
        if digest(arguments) != digest(committed_args):
            raise PermissionError("EABC_REQUEST_DIGEST_MISMATCH")
        forwarded.append(arguments.copy())
        return json.dumps({"ok": True})

    proxy._forward_to_upstream = eabc_gate

    with pytest.raises(PermissionError, match="EABC_REQUEST_DIGEST_MISMATCH"):
        await proxy.call_tool(
            call_id, "test.echo", {"message": "tampered"}
        )

    assert forwarded == []
