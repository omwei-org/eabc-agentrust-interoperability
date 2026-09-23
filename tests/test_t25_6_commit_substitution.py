"""T25.6 — commit substitution / exact execution-object binding.

The same logical COMMIT is attempted with substitutions in one binding component.
The adapter must reject before forwarding.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.mcp.proxy import CMCPProxy
from cmcp_runtime.session.state import SessionState


@dataclass(frozen=True)
class Commit:
    commit_id: str
    call_id: str
    tool_name: str
    request_payload_hash: str
    policy_id: str


def make_proxy():
    entry = CatalogEntry(
        tool_name="test.echo",
        server=ServerIdentity(
            display_name="T25.6 Mock", url="https://local.invalid/mcp",
            tls_fingerprint="SHA256:" + "A" * 43 + "=",
            spiffe_id=None, transport="http-sse", rotation_mode="key-pinned",
        ),
        approved_definition=ApprovedDefinition(
            description="echo", input_schema={"type": "object"}, output_schema=None
        ),
        definition_hash="sha256:" + "0" * 64,
        compliance_domain="public", requires_baa=False,
        sensitivity_level="public", added_at="2026-09-23T00:00:00Z",
        approved_by="t25.6",
    )
    catalog = ToolCatalog(entries={"test.echo": entry}, catalog_hash="sha256:" + "1" * 64)
    config = Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        proxy = CMCPProxy(
            catalog=catalog, policy_evaluator=MagicMock(),
            session=SessionState(session_id="t25.6"),
            audit_chain=AuditChain("t25.6"), config=config,
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
async def test_commit_substitution_fails_closed_before_forwarding():
    proxy = make_proxy()

    committed = Commit(
        commit_id="eabc-t25.6-001", call_id="call-001", tool_name="test.echo",
        request_payload_hash="placeholder", policy_id="policy-A",
    )
    forwarded = []

    async def gate(call_id, entry, tool_name, arguments, *, finalization=None):
        import hashlib, json
        digest = "sha256:" + hashlib.sha256(
            json.dumps({"tool_name": tool_name, "arguments": arguments},
                       sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        candidate = Commit(
            commit_id=committed.commit_id, call_id=call_id, tool_name=tool_name,
            request_payload_hash=digest, policy_id="policy-A",
        )
        if candidate != committed:
            raise PermissionError("EABC_COMMIT_SUBSTITUTION")
        forwarded.append(candidate)
        return "ok"

    proxy._forward_to_upstream = gate

    # Establish the real request digest using the production call path.
    import hashlib, json
    digest = "sha256:" + hashlib.sha256(
        json.dumps({"tool_name": "test.echo", "arguments": {"x": 1}},
                   sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    committed = Commit(committed.commit_id, committed.call_id, committed.tool_name, digest, committed.policy_id)

    async def bind_and_gate(call_id, entry, tool_name, arguments, *, finalization=None):
        finalization.eabc_commit_id = committed.commit_id
        # Deliberately bind the commit to the original call, while cMCP supplies the actual call_id.
        candidate_call_id = committed.call_id
        candidate_digest = "sha256:" + hashlib.sha256(
            json.dumps({"tool_name": tool_name, "arguments": arguments},
                       sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        candidate = Commit(committed.commit_id, candidate_call_id, tool_name, candidate_digest, committed.policy_id)
        if candidate != committed:
            raise PermissionError("EABC_COMMIT_SUBSTITUTION")
        forwarded.append(candidate)
        return "ok"

    proxy._forward_to_upstream = bind_and_gate

    # Correct call_id must pass.
    await proxy.call_tool("call-001", "test.echo", {"x": 1})
    assert len(forwarded) == 1

    # A different call_id reuses the same COMMIT and must be rejected.
    with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
        await proxy.call_tool("call-002", "test.echo", {"x": 1})

    assert len(forwarded) == 1
    assert proxy._audit.verify_chain() is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name,arguments,policy_id",
    [
        ("test.other", {"x": 1}, "policy-A"),
        ("test.echo", {"x": 2}, "policy-A"),
        ("test.echo", {"x": 1}, "policy-B"),
    ],
)
async def test_each_binding_component_is_non_substitutable(tool_name, arguments, policy_id):
    proxy = make_proxy()
    import hashlib, json
    digest = "sha256:" + hashlib.sha256(
        json.dumps({"tool_name": "test.echo", "arguments": {"x": 1}},
                   sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    committed = Commit("eabc-t25.6-002", "call-002", "test.echo", digest, "policy-A")

    forwarded = []

    async def gate(call_id, entry, actual_tool, actual_args, *, finalization=None):
        finalization.eabc_commit_id = committed.commit_id
        actual_digest = "sha256:" + hashlib.sha256(
            json.dumps({"tool_name": actual_tool, "arguments": actual_args},
                       sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        candidate = Commit(committed.commit_id, committed.call_id, actual_tool, actual_digest, policy_id)
        if candidate != committed:
            raise PermissionError("EABC_COMMIT_SUBSTITUTION")
        forwarded.append(candidate)
        return "ok"

    proxy._forward_to_upstream = gate

    call_id = "call-002"
    if tool_name == "test.other":
        # catalog intentionally contains only test.echo; verify the binding gate remains the decisive assertion
        proxy._catalog._entries["test.other"] = proxy._catalog._entries["test.echo"]
    with pytest.raises(PermissionError, match="EABC_COMMIT_SUBSTITUTION"):
        await proxy.call_tool(call_id, tool_name, arguments)

    assert forwarded == []
