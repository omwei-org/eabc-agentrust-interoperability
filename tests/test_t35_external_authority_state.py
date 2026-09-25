"""T35 external authority-state provider experiment at the real forwarding seam."""
import asyncio
import json
import threading
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import action_binding_digest, request_digest
from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.session.state import SessionState


class ExternalAuthority:
    def __init__(self):
        self.epoch = 1
        self.available = True
        self.lock = threading.Lock()

    def snapshot(self):
        with self.lock:
            if not self.available:
                raise RuntimeError("authority_unavailable")
            return self.epoch

    def revoke(self):
        with self.lock:
            self.epoch += 1


class CachedAuthority:
    def __init__(self, source):
        self.source = source
        self.epoch = source.snapshot()

    def refresh(self):
        self.epoch = self.source.snapshot()

    def current_epoch(self):
        return self.epoch


class FailClosedAuthority:
    def __init__(self, source):
        self.source = source
    def current_epoch(self):
        return self.source.snapshot()


def _sink(path: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            n=int(self.headers.get("Content-Length","0")); self.rfile.read(n)
            body=json.dumps({"jsonrpc":"2.0","id":1,"result":{"ok":True}}).encode()
            self.send_response(200); self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(body))); self.end_headers()
            self.wfile.write(body)
            with path.open("a",encoding="utf-8") as f: f.write("{\"ok\":true}\n")
        def log_message(self,*_): pass
    s=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    threading.Thread(target=s.serve_forever,daemon=True).start()
    return s,f"http://127.0.0.1:{s.server_port}/mcp"


def _proxy(url):
    from cmcp_runtime.mcp.proxy import CMCPProxy
    entry=CatalogEntry(
        tool_name="test.effect",
        server=ServerIdentity(display_name="T35 Sink",url=url,
            tls_fingerprint="SHA256:"+"A"*43+"=",spiffe_id=None,
            transport="http-sse",rotation_mode="key-pinned"),
        approved_definition=ApprovedDefinition(description="effect",
            input_schema={"type":"object"},output_schema=None),
        definition_hash="sha256:"+"0"*64,compliance_domain="public",
        requires_baa=False,sensitivity_level="public",
        added_at="2026-09-25T00:00:00Z",approved_by="t35")
    catalog=ToolCatalog(entries={"test.effect":entry},catalog_hash="sha256:"+"1"*64)
    config=Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"),patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        p=CMCPProxy(catalog=catalog,policy_evaluator=MagicMock(),
            session=SessionState(session_id="t35-agent"),
            audit_chain=AuditChain("t35"),config=config)
    p._check_health=MagicMock(return_value=None)
    p._check_upstream_drift=AsyncMock(return_value=False)
    p._policy.evaluate.return_value=MagicMock(rule_matched="test.allow",would_have_denied=False,advice={})
    p._mcp_gateway.intercept_tool_call.return_value=(True,"")
    p._mcp_gateway.intercept_tool_response.return_value=MagicMock(threats=[],content=None,allowed=True)
    p._policy.authorize_egress.return_value=MagicMock(would_have_denied=False)
    return p


def _commit(p,epoch,eid,cid,args,cid2):
    tool="test.effect"; policy="t35-policy"; digest=request_digest(tool,args)
    return EABCCommit(commit_id=cid2,call_id=cid,tool_name=tool,
        request_payload_hash=digest,policy_id=policy,
        agent_identity=p._session.session_id,execution_id=eid,
        action_binding=action_binding_digest(agent_identity=p._session.session_id,
            execution_id=eid,tool_name=tool,request_payload_hash=digest,policy_id=policy),
        authority_ref="authority-t35",authority_epoch=epoch)


async def invoke(p,cid,args,eid):
    return await p.call_tool(cid,"test.effect",args,execution_id=eid)


def instrument(p,c):
    original=p._forward_to_upstream
    async def wrapped(*a,**kw):
        c["forwarding"]+=1
        return await original(*a,**kw)
    p._forward_to_upstream=wrapped


def setup(p,provider,commit):
    p._t35_authority_provider=provider
    p._t35_adapter=EABCMCPAdapter()
    p._t35_commit=commit
    p._t35_policy_id="t35-policy"


@pytest.mark.asyncio
async def test_t35_a_external_authority_stable(tmp_path):
    s,url=_sink(tmp_path/"a"); src=ExternalAuthority()
    try:
        p=_proxy(url); setup(p,FailClosedAuthority(src),_commit(p,1,"e-a","c-a",{"v":1},"m-a"))
        c={"forwarding":0}; instrument(p,c)
        r=await invoke(p,"c-a",{"v":1},"e-a")
        assert r.allowed is True and c["forwarding"]==1
        assert len((tmp_path/"a").read_text().splitlines())==1
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t35_b_external_revocation_observed(tmp_path):
    s,url=_sink(tmp_path/"b"); src=ExternalAuthority()
    try:
        p=_proxy(url); src.revoke()
        setup(p,FailClosedAuthority(src),_commit(p,1,"e-b","c-b",{"v":2},"m-b"))
        c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_EPOCH_MISMATCH"):
            await invoke(p,"c-b",{"v":2},"e-b")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t35_c_stale_cache_fails_closed(tmp_path):
    s,url=_sink(tmp_path/"c"); src=ExternalAuthority(); cache=CachedAuthority(src)
    try:
        p=_proxy(url); src.revoke()
        setup(p,cache,_commit(p,2,"e-c","c-c",{"v":3},"m-c"))
        c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_EPOCH_MISMATCH"):
            await invoke(p,"c-c",{"v":3},"e-c")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t35_d_unavailable_fails_closed(tmp_path):
    s,url=_sink(tmp_path/"d"); src=ExternalAuthority(); src.available=False
    try:
        p=_proxy(url); setup(p,FailClosedAuthority(src),_commit(p,1,"e-d","c-d",{"v":4},"m-d"))
        c={"forwarding":0}; instrument(p,c)
        with pytest.raises(RuntimeError,match="authority_unavailable"):
            await invoke(p,"c-d",{"v":4},"e-d")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t35_e_new_epoch_after_refresh(tmp_path):
    s,url=_sink(tmp_path/"e"); src=ExternalAuthority(); cache=CachedAuthority(src)
    try:
        p=_proxy(url); src.revoke(); cache.refresh()
        setup(p,cache,_commit(p,2,"e-e","c-e",{"v":5},"m-e"))
        c={"forwarding":0}; instrument(p,c)
        r=await invoke(p,"c-e",{"v":5},"e-e")
        assert r.allowed is True and c["forwarding"]==1
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t35_f_two_boundaries_same_authoritative_revocation(tmp_path):
    s,url=_sink(tmp_path/"f"); src=ExternalAuthority()
    try:
        p1=_proxy(url); p2=_proxy(url); src.revoke()
        for i,p in enumerate((p1,p2)):
            setup(p,FailClosedAuthority(src),_commit(p,2,f"e-f-{i}",f"c-f-{i}",{"v":6},f"m-f-{i}"))
        counts=[{"forwarding":0},{"forwarding":0}]
        instrument(p1,counts[0]); instrument(p2,counts[1])
        results=await asyncio.gather(
            invoke(p1,"c-f-0",{"v":6},"e-f-0"),
            invoke(p2,"c-f-1",{"v":6},"e-f-1"),
            return_exceptions=True)
        assert all(isinstance(x,PermissionError) for x in results)
        assert sum(x["forwarding"] for x in counts)==0
    finally:s.shutdown()
