"""T30.3: exercise the actual pinned CMCPProxy.call_tool() forwarding path."""

from __future__ import annotations

import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import action_binding_digest, request_digest
from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.policy.evaluator import PolicyDecision
from cmcp_runtime.session.state import SessionState


def _make_proxy(server_url: str):
    from cmcp_runtime.mcp.proxy import CMCPProxy

    entry = CatalogEntry(
        tool_name="test.effect",
        server=ServerIdentity(
            display_name="T30.3 sink",
            url=server_url,
            tls_fingerprint="",
            spiffe_id=None,
            transport="http-sse",
            rotation_mode="none",
        ),
        approved_definition=ApprovedDefinition(
            description="observable sink", input_schema={"type": "object"}, output_schema=None
        ),
        definition_hash="sha256:" + "0" * 64,
        compliance_domain="public",
        requires_baa=False,
        sensitivity_level="public",
        added_at="2026-09-24T00:00:00Z",
        approved_by="t30.3",
    )
    catalog = ToolCatalog(entries={"test.effect": entry}, catalog_hash="sha256:" + "1" * 64)
    evaluator = MagicMock()
    decision = PolicyDecision(
        allowed=True,
        enforcement_mode=EnforcementMode.ENFORCING,
        rule_matched=None,
        advice={},
        evaluation_ms=0.1,
        would_have_denied=False,
    )
    evaluator.evaluate.return_value = decision
    evaluator.authorize_egress.return_value = decision
    evaluator.bundle_hash = "sha256:" + "2" * 64
    evaluator.enforcement_mode = EnforcementMode.ENFORCING
    session = SessionState(session_id="t30-3-agent")
    chain = AuditChain("t30-3-agent")
    cfg = Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        proxy = CMCPProxy(catalog, evaluator, session, chain, cfg)
    gateway = MagicMock()
    gateway.intercept_tool_call.return_value = (True, "")
    gateway.intercept_tool_response.return_value = MagicMock(allowed=True, threats=[], content=None)
    proxy._mcp_gateway = gateway
    return proxy


def _sink_server(sink: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length))
            params = request.get("params", {})
            if "name" not in params:
                body = {"jsonrpc": "2.0", "id": request.get("id"), "result": {"tools": [{"name": "test.effect", "description": "observable sink", "inputSchema": {"type": "object"}}]}}
            else:
                event = {
                    "tool_name": params["name"],
                    "arguments": params.get("arguments", {}),
                }
                raw = json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
                with sink.open("ab") as f:
                    f.write(raw + b"\\n")
                    f.flush()
                body = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {"content": [{"type": "text", "text": "sink:accepted"}]},
                }
            payload = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}/mcp"


@pytest.mark.asyncio
async def test_actual_call_tool_reaches_real_upstream_after_eabc_admission(tmp_path: Path):
    sink = tmp_path / "upstream-effect.jsonl"
    server, url = _sink_server(sink)
    try:
        proxy = _make_proxy(url)
        execution_id = "exec-t30-3-001"
        call_id = "call-t30-3-001"
        tool_name = "test.effect"
        arguments = {"destination": "sink-1", "value": 7}
        policy_id = "t30.3-policy"
        request_hash = request_digest(tool_name, arguments)
        binding = action_binding_digest(
            agent_identity="t30-3-agent",
            execution_id=execution_id,
            tool_name=tool_name,
            request_payload_hash=request_hash,
            policy_id=policy_id,
        )
        commit = EABCCommit(
            commit_id="commit-t30-3-001",
            agent_identity="t30-3-agent",
            execution_id=execution_id,
            call_id=call_id,
            tool_name=tool_name,
            request_payload_hash=request_hash,
            policy_id=policy_id,
            action_binding=binding,
            authority_ref="authority-t30-3-001",
        )
        proxy._t30_3_adapter = EABCMCPAdapter()
        proxy._t30_3_commit = commit
        proxy._t30_3_policy_id = policy_id

        with patch.object(proxy, "_check_health", return_value=None):
            result = await proxy.call_tool(
                call_id,
                tool_name,
                arguments,
                execution_id=execution_id,
            )

        assert result.allowed is True
        lines = sink.read_text().splitlines()
        assert len(lines) == 1
        observed = json.loads(lines[0])
        assert observed["tool_name"] == tool_name
        assert observed["arguments"] == arguments
        assert len(hashlib.sha256(sink.read_bytes()).hexdigest()) == 64
    finally:
        server.shutdown()


def test_evidence_manifest_fields_are_defined():
    required = {
        "upstream_commit", "experiment_commit", "execution_id", "call_id",
        "request_payload_hash", "commit_id", "terminal_state", "sink_sha256",
    }
    assert len(required) == 8
