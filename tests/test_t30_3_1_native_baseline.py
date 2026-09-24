"""Native pinned cMCP baseline for T30.3.1."""

from pathlib import Path
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


import pytest
from cmcp_runtime.mcp.proxy import CMCPProxy
def _sink_server(sink: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length))
            with sink.open("ab") as f:
                f.write(json.dumps(request, sort_keys=True).encode() + b"\n")
            body = {"jsonrpc": "2.0", "id": request["id"], "result": {"content": [{"type": "text", "text": "ok"}]}}
            payload = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}/mcp"


def _make_proxy(server_url: str):
    from unittest.mock import MagicMock, patch
    from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
    from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
    from cmcp_runtime.policy.evaluator import PolicyDecision
    from cmcp_runtime.session.state import SessionState
    from cmcp_runtime.audit.chain import AuditChain

    entry = CatalogEntry(tool_name="test.effect", server=ServerIdentity(display_name="sink", url=server_url, tls_fingerprint="", spiffe_id=None, transport="http-sse", rotation_mode="none"), approved_definition=ApprovedDefinition(description="sink", input_schema={"type":"object"}, output_schema=None), definition_hash="sha256:"+"0"*64, compliance_domain="public", requires_baa=False, sensitivity_level="public", added_at="2026-09-24T00:00:00Z", approved_by="baseline")
    catalog = ToolCatalog(entries={"test.effect": entry}, catalog_hash="sha256:"+"1"*64)
    evaluator = MagicMock()
    decision = PolicyDecision(allowed=True, enforcement_mode=EnforcementMode.ENFORCING, rule_matched=None, advice={}, evaluation_ms=0.1, would_have_denied=False)
    evaluator.evaluate.return_value = decision
    evaluator.authorize_egress.return_value = decision
    evaluator.bundle_hash = "sha256:"+"2"*64
    evaluator.enforcement_mode = EnforcementMode.ENFORCING
    session = SessionState(session_id="native-baseline")
    chain = AuditChain("native-baseline")
    cfg = Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        proxy = CMCPProxy(catalog, evaluator, session, chain, cfg)
    return proxy





@pytest.mark.asyncio
async def test_native_valid_execution_id_is_fail_closed_before_upstream(tmp_path: Path):
    sink = tmp_path / "native-baseline.jsonl"
    server, url = _sink_server(sink)
    try:
        proxy = _make_proxy(url)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(proxy, "_check_health", lambda: None)
            result = await proxy.call_tool(
                "native-baseline-call",
                "test.effect",
                {"destination": "native-baseline", "value": 0},
                execution_id="native-baseline-execution",
            )
        assert result.allowed is False
        assert not sink.exists() or sink.read_text() == ""
    finally:
        server.shutdown()
