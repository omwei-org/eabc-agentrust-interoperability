"""EABC interoperability tests against the pinned cMCP runtime.

These tests intentionally exercise CMCPProxy itself rather than reimplementing
its control logic. The policy evaluator and AGT gateway are isolated at their
documented seams so the tests answer narrow execution-boundary questions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import (
    ApprovedDefinition,
    CatalogEntry,
    ServerIdentity,
    ToolCatalog,
)
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.errors import PolicyDeny
from cmcp_runtime.mcp.proxy import CMCPProxy
from cmcp_runtime.policy.evaluator import PolicyDecision, PolicyEvaluator
from cmcp_runtime.session.state import SessionState


def _entry(tool_name: str = "test.echo") -> CatalogEntry:
    return CatalogEntry(
        tool_name=tool_name,
        server=ServerIdentity(
            display_name="EABC test upstream",
            url="http://127.0.0.1:9999/mcp",
            tls_fingerprint="SHA256:AAAA/BBBB==",
            spiffe_id=None,
            transport="http-sse",
            rotation_mode="key-pinned",
        ),
        approved_definition=ApprovedDefinition(
            description="echo",
            input_schema={"type": "object"},
            output_schema=None,
        ),
        definition_hash="sha256:" + "0" * 64,
        compliance_domain="external",
        requires_baa=False,
        sensitivity_level="public",
        added_at="2026-09-23T00:00:00Z",
        approved_by="eabc-test",
    )


def _evaluator(*, allow: bool) -> MagicMock:
    ev = MagicMock(spec=PolicyEvaluator)
    if allow:
        ev.evaluate.return_value = PolicyDecision(
            allowed=True,
            enforcement_mode=EnforcementMode.ENFORCING,
            rule_matched=None,
            advice={},
            evaluation_ms=0.1,
            would_have_denied=False,
        )
    else:
        ev.evaluate.side_effect = PolicyDeny("denied by test policy")
    ev.authorize_egress.return_value = PolicyDecision(
        allowed=True,
        enforcement_mode=EnforcementMode.ENFORCING,
        rule_matched=None,
        advice={},
        evaluation_ms=0.1,
        would_have_denied=False,
    )
    ev.bundle_hash = "sha256:" + "0" * 64
    ev.enforcement_mode = EnforcementMode.ENFORCING
    return ev


def _proxy(*, allow: bool):
    entry = _entry()
    catalog = ToolCatalog(
        entries={"test.echo": entry},
        catalog_hash="sha256:" + "1" * 64,
    )
    session = SessionState(session_id="eabc-t01")
    chain = AuditChain("eabc-t01")
    cfg = Config()
    cfg.attestation = AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING)

    proxy = CMCPProxy(
        catalog,
        _evaluator(allow=allow),
        session,
        chain,
        cfg,
        attestation_platform="software-only",
    )

    proxy._mcp_gateway = MagicMock()
    proxy._mcp_gateway.intercept_tool_call.return_value = (True, "ok")
    proxy._mcp_gateway.intercept_tool_response.return_value = MagicMock(
        allowed=True,
        content="echo:ok",
        threats=[],
        action="allowed",
    )
    proxy._forward_to_upstream = AsyncMock(return_value="echo:ok")
    return proxy, chain


@pytest.mark.asyncio
async def test_t01_allow_commit_candidate_and_effect():
    """T01: an authorized call reaches the forwarding seam and returns effect."""

    proxy, chain = _proxy(allow=True)
    arguments = {"message": "hello", "position": [1, 2, 3]}

    result = await proxy.call_tool("cmd-t01", "test.echo", arguments)

    assert result.allowed is True
    proxy._forward_to_upstream.assert_awaited_once()
    call = proxy._forward_to_upstream.await_args
    assert call.args[0] == "cmd-t01"
    assert call.args[2] == "test.echo"
    assert call.args[3] == arguments

    tool_entries = [e for e in chain.entries if e.entry_type == "tool_call"]
    assert tool_entries
    assert tool_entries[-1].policy_decision == "allow"


@pytest.mark.asyncio
async def test_t02_deny_produces_no_forward_and_no_effect():
    """T02: policy denial stops the path before upstream forwarding."""

    proxy, chain = _proxy(allow=False)

    result = await proxy.call_tool("cmd-t02", "test.echo", {"message": "blocked"})

    assert result.allowed is False
    proxy._forward_to_upstream.assert_not_awaited()

    tool_entries = [e for e in chain.entries if e.entry_type == "tool_call"]
    assert tool_entries
    assert tool_entries[-1].policy_decision == "deny"


@pytest.mark.asyncio
async def test_t01_exact_arguments_reach_forwarding_seam():
    """The execution request at the forwarding seam is the request authorized
    by the proxy call; no alternate argument object is substituted by the
    CMCPProxy path exercised here."""

    proxy, _ = _proxy(allow=True)
    request = {
        "amount": 7,
        "destination": "cell-3",
        "mode": "move",
    }

    await proxy.call_tool("cmd-binding", "test.echo", request)

    forwarded = proxy._forward_to_upstream.await_args.args[3]
    assert forwarded == request
