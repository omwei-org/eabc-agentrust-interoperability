from unittest.mock import AsyncMock, MagicMock

import pytest

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.mcp.proxy import CMCPProxy
from cmcp_runtime.policy.evaluator import PolicyDecision, PolicyEvaluator
from cmcp_runtime.session.state import SessionState

def _proxy():
    entry = CatalogEntry(tool_name='test.echo', server=ServerIdentity(display_name='T03', url='http://127.0.0.1:9999/mcp', tls_fingerprint='SHA256:AAAA/BBBB==', spiffe_id=None, transport='http-sse', rotation_mode='key-pinned'), approved_definition=ApprovedDefinition(description='echo', input_schema={'type':'object'}, output_schema=None), definition_hash='sha256:'+'0'*64, compliance_domain='external', requires_baa=False, sensitivity_level='public', added_at='2026-09-23T00:00:00Z', approved_by='eabc-t03')
    catalog = ToolCatalog(entries={'test.echo': entry}, catalog_hash='sha256:'+'1'*64)
    evaluator = MagicMock(spec=PolicyEvaluator)
    decision = PolicyDecision(allowed=True, enforcement_mode=EnforcementMode.ENFORCING, rule_matched=None, advice={}, evaluation_ms=0.1, would_have_denied=False)
    evaluator.evaluate.return_value = decision
    evaluator.authorize_egress.return_value = decision
    evaluator.bundle_hash = 'sha256:'+'0'*64
    evaluator.enforcement_mode = EnforcementMode.ENFORCING
    cfg = Config()
    cfg.attestation = AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING)
    proxy = CMCPProxy(catalog, evaluator, SessionState(session_id='eabc-t03'), AuditChain('eabc-t03'), cfg, attestation_platform='software-only')
    proxy._mcp_gateway = MagicMock()
    proxy._mcp_gateway.intercept_tool_call.return_value = (True, 'ok')
    proxy._mcp_gateway.intercept_tool_response.return_value = MagicMock(allowed=True, content='echo:ok', threats=[], action='allowed')
    proxy._forward_to_upstream = AsyncMock(return_value='echo:ok')
    return proxy

@pytest.mark.asyncio
async def test_t03_authorized_request_equals_forwarded_request():
    proxy = _proxy()
    authorized = {'amount': 7, 'destination': 'cell-3', 'mode': 'move'}
    await proxy.call_tool('cmd-t03', 'test.echo', authorized)
    forwarded = proxy._forward_to_upstream.await_args.args[3]
    assert forwarded == authorized

@pytest.mark.asyncio
async def test_t03_substitution_negative_control():
    proxy = _proxy()
    authorized = {'amount': 7, 'destination': 'cell-3', 'mode': 'move'}
    substituted = {'amount': 7000, 'destination': 'cell-9', 'mode': 'move'}
    await proxy.call_tool('cmd-t03-negative', 'test.echo', authorized)
    forwarded = proxy._forward_to_upstream.await_args.args[3]
    assert forwarded == authorized
    assert forwarded != substituted
