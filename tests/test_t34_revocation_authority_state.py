"""T34 revocation / authority-state race against the real CMCPProxy forwarding seam."""
import asyncio
import json
import threading
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import action_binding_digest, request_digest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.session.state import SessionState


class AuthorityState:
    def __init__(self):
        self.epoch = 1
        self.revoked = False
        self.lock = threading.Lock()

    def revoke(self):
        with self.lock:
            self.revoked = True
            self.epoch += 1

    def snapshot(self):
        with self.lock:
            return self.epoch, self.revoked


def _sink(path: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(n)
            body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            with path.open("a", encoding="utf-8") as f:
                f.write("{\"ok\":true}\n")
        def log_message(self, *_args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}/mcp"


def _proxy(url):
    from cmcp_runtime.mcp.proxy import CMCPProxy
    entry = CatalogEntry(
        tool_name="test.effect",
        server=ServerIdentity(display_name="T34 Sink", url=url,
            tls_fingerprint="SHA256:" + "A" * 43 + "=", spiffe_id=None,
            transport="http-sse", rotation_mode="key-pinned"),
        approved_definition=ApprovedDefinition(description="effect",
            input_schema={"type":"object"}, output_schema=None),
        definition_hash="sha256:"+"0"*64, compliance_domain="public",
        requires_baa=False, sensitivity_level="public",
        added_at="2026-09-25T00:00:00Z", approved_by="t34")
    catalog=ToolCatalog(entries={"test.effect":entry}, catalog_hash="sha256:"+"1"*64)
    config=Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"), patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        p=CMCPProxy(catalog=catalog, policy_evaluator=MagicMock(),
            session=SessionState(session_id="t34-agent"),
            audit_chain=AuditChain("t34"), config=config)
    p._check_health=MagicMock(return_value=None)
    p._check_upstream_drift=AsyncMock(return_value=False)
    p._policy.evaluate.return_value=MagicMock(rule_matched="test.allow",would_have_denied=False,advice={})
    p._mcp_gateway.intercept_tool_call.return_value=(True,"")
    p._mcp_gateway.intercept_tool_response.return_value=MagicMock(threats=[],content=None,allowed=True)
    p._policy.authorize_egress.return_value=MagicMock(would_have_denied=False)
    return p


def _commit(proxy, epoch, execution_id, call_id, args, commit_id):
    tool="test.effect"; policy="t34-policy"; digest=request_digest(tool,args)
    return EABCCommit(commit_id=commit_id, call_id=call_id, tool_name=tool,
        request_payload_hash=digest, policy_id=policy,
        agent_identity=proxy._session.session_id, execution_id=execution_id,
        action_binding=action_binding_digest(agent_identity=proxy._session.session_id,
            execution_id=execution_id, tool_name=tool,
            request_payload_hash=digest, policy_id=policy),
        authority_ref="authority-t34", authority_epoch=epoch)


async def _invoke(proxy, call_id, args, execution_id):
    return await proxy.call_tool(call_id,"test.effect",args,execution_id=execution_id)


def _instrument(proxy, counter):
    original=proxy._forward_to_upstream
    async def wrapped(*a,**kw):
        counter["forwarding_entry_count"] += 1
        return await original(*a,**kw)
    proxy._forward_to_upstream=wrapped


@pytest.mark.asyncio
async def test_t34_a_stable_authority(tmp_path):
    server,url=_sink(tmp_path/"a.jsonl")
    try:
        p=_proxy(url); state=AuthorityState()
        p._t34_authority_epoch=state.epoch; p._t34_adapter=EABCMCPAdapter()
        p._t34_commit=_commit(p,1,"exec-a","call-a",{"v":1},"commit-a")
        p._t34_policy_id="t34-policy"; c={"forwarding_entry_count":0}; _instrument(p,c)
        r=await _invoke(p,"call-a",{"v":1},"exec-a")
        assert r.allowed is True and c["forwarding_entry_count"]==1
        assert len((tmp_path/"a.jsonl").read_text().splitlines())==1
    finally: server.shutdown()


@pytest.mark.asyncio
async def test_t34_b_revoked_before_admission(tmp_path):
    server,url=_sink(tmp_path/"b.jsonl")
    try:
        p=_proxy(url); state=AuthorityState(); state.revoke()
        p._t34_authority_epoch=state.epoch; p._t34_adapter=EABCMCPAdapter()
        p._t34_commit=_commit(p,1,"exec-b","call-b",{"v":2},"commit-b")
        c={"forwarding_entry_count":0}; _instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_EPOCH_MISMATCH"):
            await _invoke(p,"call-b",{"v":2},"exec-b")
        assert c["forwarding_entry_count"]==0
    finally: server.shutdown()


@pytest.mark.asyncio
async def test_t34_c_revoked_between_prepare_and_finalize(tmp_path):
    server,url=_sink(tmp_path/"c.jsonl")
    try:
        p=_proxy(url); state=AuthorityState()
        p._t34_authority_epoch=state.epoch; p._t34_adapter=EABCMCPAdapter()
        p._t34_commit=_commit(p,1,"exec-c","call-c",{"v":3},"commit-c")
        def revoke_before_consume():
            state.revoke()
            p._t34_authority_epoch=state.epoch
        p._t34_before_consume=revoke_before_consume
        c={"forwarding_entry_count":0}; _instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_EPOCH_MISMATCH"):
            await _invoke(p,"call-c",{"v":3},"exec-c")
        assert c["forwarding_entry_count"]==0
        assert state.epoch==2
    finally: server.shutdown()


@pytest.mark.asyncio
async def test_t34_d_revoked_after_commit_before_forwarding(tmp_path):
    server,url=_sink(tmp_path/"d.jsonl")
    try:
        p=_proxy(url); state=AuthorityState()
        p._t34_authority_epoch=state.epoch; p._t34_adapter=EABCMCPAdapter()
        p._t34_commit=_commit(p,1,"exec-d","call-d",{"v":4},"commit-d")
        # The commit exists, but authority state is changed before consume.
        state.revoke(); p._t34_authority_epoch=state.epoch
        c={"forwarding_entry_count":0}; _instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_EPOCH_MISMATCH"):
            await _invoke(p,"call-d",{"v":4},"exec-d")
        assert c["forwarding_entry_count"]==0
    finally: server.shutdown()


@pytest.mark.asyncio
async def test_t34_f_epoch_bump_without_explicit_revocation(tmp_path):
    server,url=_sink(tmp_path/"f.jsonl")
    try:
        p=_proxy(url)
        p._t34_authority_epoch=1; p._t34_adapter=EABCMCPAdapter()
        p._t34_commit=_commit(p,1,"exec-f","call-f",{"v":6},"commit-f")
        p._t34_authority_epoch=2
        c={"forwarding_entry_count":0}; _instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_EPOCH_MISMATCH"):
            await _invoke(p,"call-f",{"v":6},"exec-f")
        assert c["forwarding_entry_count"]==0
    finally: server.shutdown()


def test_t34_e_concurrent_race_with_revocation(tmp_path):
    server,url=_sink(tmp_path/"e.jsonl")
    try:
        p1=_proxy(url); p2=_proxy(url); state=AuthorityState()
        shared=EABCMCPAdapter()
        commit=_commit(p1,1,"exec-e","call-e",{"v":5},"commit-e")
        for p in (p1,p2):
            p._t34_authority_epoch=state.epoch; p._t34_adapter=shared
            p._t34_commit=commit; p._t34_policy_id="t34-policy"
        start=threading.Event(); results=[None,None]
        def worker(i):
            async def run():
                try:
                    await _invoke((p1,p2)[i],"call-e",{"v":5},"exec-e")
                    return True
                except PermissionError:
                    return False
            start.wait()
            results[i]=asyncio.run(run())
        threads=[threading.Thread(target=worker,args=(i,)) for i in range(2)]
        for t in threads:t.start()
        start.set()
        state.revoke()
        for p in (p1,p2): p._t34_authority_epoch=state.epoch
        for t in threads:t.join(timeout=15)
        # Revocation is deterministically applied before either worker can
        # complete a valid consume because the shared epoch is bumped first.
        assert all(not t.is_alive() for t in threads)
        assert sum(bool(x) for x in results)==0
        assert not (tmp_path/"e.jsonl").exists() or not (tmp_path/"e.jsonl").read_text()
    finally: server.shutdown()
