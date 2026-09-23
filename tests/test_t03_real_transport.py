from __future__ import annotations

import hashlib
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.mcp.proxy import CMCPProxy
from cmcp_runtime.mcp.streamable_http import build_request
from cmcp_runtime.policy.evaluator import PolicyDecision, PolicyEvaluator
from cmcp_runtime.session.state import SessionState
from harness.mock_mcp_server import CaptureServer


def _entry(url: str) -> CatalogEntry:
    return CatalogEntry(
        tool_name="test.echo",
        server=ServerIdentity(
            display_name="EABC transport capture",
            url=url,
            tls_fingerprint="SHA256:AAAA/BBBB==",
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
        approved_by="eabc-t03",
    )


def _real_forward_proxy(url: str) -> CMCPProxy:
    entry = _entry(url)
    catalog = ToolCatalog(entries={"test.echo": entry}, catalog_hash="sha256:" + "1" * 64)
    decision = PolicyDecision(
        allowed=True, enforcement_mode=EnforcementMode.ENFORCING,
        rule_matched=None, advice={}, evaluation_ms=0.1, would_have_denied=False
    )
    evaluator = MagicMock(spec=PolicyEvaluator)
    evaluator.evaluate.return_value = decision
    evaluator.authorize_egress.return_value = decision
    evaluator.bundle_hash = "sha256:" + "0" * 64
    evaluator.enforcement_mode = EnforcementMode.ENFORCING
    config = Config()
    config.attestation = AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING)
    proxy = CMCPProxy(
        catalog, evaluator, SessionState(session_id="eabc-t03-transport"),
        AuditChain("eabc-t03-transport"), config, attestation_platform="software-only"
    )
    proxy._check_upstream_drift = AsyncMock(return_value=False)
    proxy._mcp_gateway = MagicMock()
    proxy._mcp_gateway.intercept_tool_call.return_value = (True, "ok")
    proxy._mcp_gateway.intercept_tool_response.return_value = MagicMock(
        allowed=True, content="capture-ok", threats=[], action="allowed"
    )
    return proxy


@pytest.mark.asyncio
async def test_t03_real_cmcp_forwarding_reaches_execution_domain():
    server = CaptureServer()
    server.start()
    proxy = _real_forward_proxy(server.url)
    try:
        call_id = "cmd-t03-real-transport"
        tool = "test.echo"
        arguments = {"amount": 7, "destination": "cell-3", "mode": "move"}

        result = await proxy.call_tool(call_id, tool, arguments)

        assert result.allowed is True
        assert len(server.captured) == 1
        received = server.captured[0]["payload"]
        expected, _headers = build_request(
            call_id, "tools/call", {"name": tool, "arguments": arguments}
        )
        assert received == expected

        expected_digest = hashlib.sha256(
            json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        received_digest = hashlib.sha256(
            json.dumps(received, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        assert expected_digest == received_digest
    finally:
        await proxy.aclose()
        server.stop()
