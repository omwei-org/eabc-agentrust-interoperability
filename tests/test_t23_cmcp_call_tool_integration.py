"""T23 disposable integration against the real cMCP CMCPProxy.call_tool path."""

from __future__ import annotations

import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import (
    ApprovedDefinition,
    CatalogEntry,
    ServerIdentity,
    ToolCatalog,
)
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.session.state import SessionState


def digest(arguments):
    return "sha256:" + hashlib.sha256(
        json.dumps(arguments, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class EABCGatedProxy:
    """Disposable wrapper: production CMCPProxy.call_tool remains untouched."""

    def __init__(self, proxy):
        self.proxy = proxy
        self.effects = []
        self.commits = {}

    def prepare_commit(self, call_id, tool_name, arguments):
        self.commits[call_id] = {
            "commit_id": f"eabc-{call_id}",
            "call_id": call_id,
            "tool_name": tool_name,
            "request_payload_hash": digest(arguments),
        }

    def install(self):
        original = self.proxy._forward_to_upstream

        async def gated_forward(call_id, entry, tool_name, arguments, **kwargs):
            commit = self.commits.get(call_id)
            if commit is None:
                raise PermissionError("NO_COMMIT")
            if commit["tool_name"] != tool_name:
                raise PermissionError("TOOL_MISMATCH")
            if commit["request_payload_hash"] != digest(arguments):
                raise PermissionError("REQUEST_DIGEST_MISMATCH")
            self.effects.append(
                {
                    "call_id": call_id,
                    "tool_name": tool_name,
                    "arguments": arguments.copy(),
                    "commit_id": commit["commit_id"],
                }
            )
            return await original(call_id, entry, tool_name, arguments, **kwargs)

        self.proxy._forward_to_upstream = gated_forward


def make_proxy():
    from cmcp_runtime.mcp.proxy import CMCPProxy

    server = ServerIdentity(
        display_name="T23 Mock",
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
    session = SessionState(session_id="t23")
    chain = AuditChain("t23")

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
        rule_matched="test.allow",
        would_have_denied=False,
        advice={},
    )
    proxy._mcp_gateway.intercept_tool_call.return_value = (True, "")
    return proxy


@pytest.mark.asyncio
async def test_t23_real_call_tool_path_valid_commit_reaches_forwarding():
    proxy = make_proxy()
    adapter = EABCGatedProxy(proxy)
    adapter.install()

    forwarded = []

    async def mock_upstream(call_id, entry, tool_name, arguments, **kwargs):
        forwarded.append((call_id, tool_name, arguments.copy()))
        return "mock-effect"

    proxy._forward_to_upstream = adapter.proxy._forward_to_upstream
    # Keep the gate but replace the downstream method captured by it.
    original_gate = proxy._forward_to_upstream

    async def gate_to_mock(call_id, entry, tool_name, arguments, **kwargs):
        commit = adapter.commits.get(call_id)
        if commit is None:
            raise PermissionError("NO_COMMIT")
        if commit["tool_name"] != tool_name:
            raise PermissionError("TOOL_MISMATCH")
        if commit["request_payload_hash"] != digest(arguments):
            raise PermissionError("REQUEST_DIGEST_MISMATCH")
        adapter.effects.append({
            "call_id": call_id,
            "tool_name": tool_name,
            "arguments": arguments.copy(),
            "commit_id": commit["commit_id"],
        })
        return await mock_upstream(call_id, entry, tool_name, arguments, **kwargs)

    proxy._forward_to_upstream = gate_to_mock

    args = {"message": "hello"}
    adapter.prepare_commit("call-t23-001", "test.echo", args)
    result = await proxy.call_tool("call-t23-001", "test.echo", args)

    assert result.allowed is True
    assert forwarded == [("call-t23-001", "test.echo", args)]
    assert len(adapter.effects) == 1
    assert adapter.effects[0]["commit_id"] == "eabc-call-t23-001"


@pytest.mark.asyncio
async def test_t23_real_call_tool_path_without_commit_has_no_effect():
    proxy = make_proxy()
    adapter = EABCGatedProxy(proxy)
    adapter.install()

    effects = []

    async def gate_only(call_id, entry, tool_name, arguments, **kwargs):
        if call_id not in adapter.commits:
            raise PermissionError("NO_COMMIT")
        effects.append(arguments.copy())
        return "mock-effect"

    proxy._forward_to_upstream = gate_only

    with pytest.raises(PermissionError, match="NO_COMMIT"):
        await proxy.call_tool(
            "call-t23-002", "test.echo", {"message": "hello"}
        )

    assert effects == []


@pytest.mark.asyncio
async def test_t23_real_call_tool_path_tampered_arguments_have_no_effect():
    proxy = make_proxy()
    adapter = EABCGatedProxy(proxy)
    adapter.install()

    effects = []

    async def gate_only(call_id, entry, tool_name, arguments, **kwargs):
        commit = adapter.commits.get(call_id)
        if commit is None or commit["request_payload_hash"] != digest(arguments):
            raise PermissionError("REQUEST_DIGEST_MISMATCH")
        effects.append(arguments.copy())
        return "mock-effect"

    proxy._forward_to_upstream = gate_only

    adapter.prepare_commit("call-t23-003", "test.echo", {"message": "hello"})

    with pytest.raises(PermissionError, match="REQUEST_DIGEST_MISMATCH"):
        await proxy.call_tool(
            "call-t23-003", "test.echo", {"message": "tampered"}
        )

    assert effects == []
