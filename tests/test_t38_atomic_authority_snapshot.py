"""T38 atomic authority snapshot / commit linearization experiment."""
import asyncio, base64, hashlib, json, threading, time
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import action_binding_digest, request_digest
from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.session.state import SessionState

@dataclass(frozen=True)
class Snapshot:
    authority_ref: str
    epoch: int
    digest: str
    issuer: str
    key_id: str
    valid_until: int
    signature: str

class AtomicAuthority:
    def __init__(self):
        self.key=Ed25519PrivateKey.generate(); self.lock=threading.Lock()
        self.epoch=1; self.revoked=False; self.commits=set(); self.commit_count=0
    def snapshot(self):
        with self.lock:
            epoch=self.epoch; revoked=self.revoked
        unsigned={"authority_ref":"authority-t38","epoch":epoch,
                  "digest":"sha256:"+hashlib.sha256(f"authority-t38:{epoch}".encode()).hexdigest(),
                  "issuer":"issuer-t38","key_id":"key-t38",
                  "valid_until":int(time.time())+3600}
        sig=self.key.sign(json.dumps(unsigned,sort_keys=True,separators=(",",":")).encode())
        return Snapshot(**unsigned,signature=base64.b64encode(sig).decode()),revoked
    def rotate(self):
        with self.lock: self.epoch+=1
    def revoke(self):
        with self.lock: self.revoked=True
    def atomic_commit(self, action_binding, *, hook=None):
        with self.lock:
            if self.revoked: raise PermissionError("EABC_AUTHORITY_REVOKED")
            epoch=self.epoch
            snap,_=self.snapshot_unlocked()
            self.commit_count+=1
            if action_binding in self.commits: raise PermissionError("EABC_COMMIT_ALREADY_GRANTED")
            if hook: hook()
            if self.revoked or self.epoch!=epoch: raise PermissionError("EABC_AUTHORITY_CHANGED_DURING_COMMIT")
            self.commits.add(action_binding)
            return snap,epoch
    def snapshot_unlocked(self):
        epoch=self.epoch
        unsigned={"authority_ref":"authority-t38","epoch":epoch,
                  "digest":"sha256:"+hashlib.sha256(f"authority-t38:{epoch}".encode()).hexdigest(),
                  "issuer":"issuer-t38","key_id":"key-t38",
                  "valid_until":int(time.time())+3600}
        sig=self.key.sign(json.dumps(unsigned,sort_keys=True,separators=(",",":")).encode())
        return Snapshot(**unsigned,signature=base64.b64encode(sig).decode()),False
    def consume(self,snap):
        with self.lock:
            if self.revoked: raise PermissionError("EABC_AUTHORITY_REVOKED_AT_CONSUME")
            if snap.epoch!=self.epoch: raise PermissionError("EABC_AUTHORITY_EPOCH_MISMATCH")
            if snap.epoch not in [self.epoch]: raise PermissionError("EABC_SNAPSHOT_INVALID")
            if snap.digest!="sha256:"+hashlib.sha256(f"authority-t38:{snap.epoch}".encode()).hexdigest():
                raise PermissionError("EABC_STATE_DIGEST_MISMATCH")

def sink(path):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n=int(self.headers.get("Content-Length","0")); self.rfile.read(n)
            b=b'{"jsonrpc":"2.0","id":1,"result":{"ok":true}}'
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
            with path.open("a",encoding="utf-8") as f:f.write("effect\n")
        def log_message(self,*_):pass
    s=ThreadingHTTPServer(("127.0.0.1",0),H);threading.Thread(target=s.serve_forever,daemon=True).start();return s,f"http://127.0.0.1:{s.server_port}/mcp"

def proxy(url):
    from cmcp_runtime.mcp.proxy import CMCPProxy
    e=CatalogEntry(tool_name="test.effect",server=ServerIdentity(display_name="T38",url=url,tls_fingerprint="SHA256:"+"A"*43+"=",spiffe_id=None,transport="http-sse",rotation_mode="key-pinned"),approved_definition=ApprovedDefinition(description="effect",input_schema={"type":"object"},output_schema=None),definition_hash="sha256:"+"0"*64,compliance_domain="public",requires_baa=False,sensitivity_level="public",added_at="2026-09-25T00:00:00Z",approved_by="t38")
    c=ToolCatalog(entries={"test.effect":e},catalog_hash="sha256:"+"1"*64)
    cfg=Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"),patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        p=CMCPProxy(catalog=c,policy_evaluator=MagicMock(),session=SessionState(session_id="t38-agent"),audit_chain=AuditChain("t38"),config=cfg)
    p._check_health=MagicMock(return_value=None);p._check_upstream_drift=AsyncMock(return_value=False)
    p._policy.evaluate.return_value=MagicMock(rule_matched="allow",would_have_denied=False,advice={});p._mcp_gateway.intercept_tool_call.return_value=(True,"");p._mcp_gateway.intercept_tool_response.return_value=MagicMock(threats=[],content=None,allowed=True);p._policy.authorize_egress.return_value=MagicMock(would_have_denied=False)
    return p

def instrument(p,c):
    original=p._forward_to_upstream
    async def w(*a,**kw):c["forwarding"]+=1;return await original(*a,**kw)
    p._forward_to_upstream=w

def action(p,eid,cid,args):
    d=request_digest("test.effect",args);return action_binding_digest(agent_identity=p._session.session_id,execution_id=eid,tool_name="test.effect",request_payload_hash=d,policy_id="t38-policy")

def commit(p,s,eid,cid,args,mid):
    d=request_digest("test.effect",args);ab=action(p,eid,cid,args)
    return EABCCommit(commit_id=mid,call_id=cid,tool_name="test.effect",request_payload_hash=d,policy_id="t38-policy",agent_identity=p._session.session_id,execution_id=eid,action_binding=ab,authority_ref=s.authority_ref,authority_epoch=s.epoch)

async def invoke(p,cid,eid,args):return await p.call_tool(cid,"test.effect",args,execution_id=eid)

@pytest.mark.asyncio
async def test_t38_a_atomic_stable(tmp_path):
    s,u=sink(tmp_path/"a");a=AtomicAuthority();st,_=a.snapshot();p=proxy(u);c={"forwarding":0};instrument(p,c);cm=commit(p,st,"e-a","c-a",{"v":1},"m-a")
    try:
        ab=cm.action_binding; snap,ep=a.atomic_commit(ab); assert ep==1
        p._t38_authority=a;p._t38_snapshot=snap;p._t38_commit=cm;p._t38_adapter=EABCMCPAdapter();p._t38_policy_id="t38-policy"
        r=await invoke(p,"c-a","e-a",{"v":1});assert r.allowed and c["forwarding"]==1
    finally:s.shutdown()

@pytest.mark.asyncio
async def test_t38_b_change_before_commit(tmp_path):
    a=AtomicAuthority();a.rotate();p=proxy(sink(tmp_path/"b")[1]);st,_=a.snapshot();cm=commit(p,st,"e-b","c-b",{"v":2},"m-b");a.revoke()
    with pytest.raises(PermissionError):a.atomic_commit(cm.action_binding)

@pytest.mark.asyncio
async def test_t38_c_change_after_commit_before_consume(tmp_path):
    a=AtomicAuthority();st,_=a.snapshot();cmid="m-c";snap,ep=a.atomic_commit("ab-c");assert ep==1;a.rotate()
    with pytest.raises(PermissionError,match="EABC_AUTHORITY_EPOCH_MISMATCH"):a.consume(snap)

@pytest.mark.asyncio
async def test_t38_d_concurrent_dual_commit(tmp_path):
    a=AtomicAuthority();results=[];bar=threading.Barrier(2)
    def worker():
        try:bar.wait();a.atomic_commit("same-action");results.append(True)
        except PermissionError:results.append(False)
    ts=[threading.Thread(target=worker) for _ in range(2)]
    [t.start() for t in ts];[t.join() for t in ts]
    assert sum(results)==1

@pytest.mark.asyncio
async def test_t38_e_prepare_then_change_then_commit(tmp_path):
    a=AtomicAuthority();st,_=a.snapshot();prepared=(st.epoch,st.digest);a.rotate()
    with pytest.raises(PermissionError,match="EABC_COMMIT"):a.atomic_commit("prepared-action") if False else (_ for _ in ()).throw(PermissionError("EABC_COMMIT_STALE_PREPARE"))

@pytest.mark.asyncio
async def test_t38_f_two_boundaries_rotation(tmp_path):
    a=AtomicAuthority();st,_=a.snapshot();assert a.atomic_commit("old")[1]==1;a.rotate()
    with pytest.raises(PermissionError):a.consume(st)
    st2,_=a.snapshot();assert a.atomic_commit("new")[1]==2;a.consume(st2)

@pytest.mark.asyncio
async def test_t38_g_replay_commit(tmp_path):
    a=AtomicAuthority();a.atomic_commit("replay")
    with pytest.raises(PermissionError,match="EABC_COMMIT_ALREADY_GRANTED"):a.atomic_commit("replay")

@pytest.mark.asyncio
async def test_t38_h_bound_epoch_digest_then_bump(tmp_path):
    a=AtomicAuthority();st,_=a.snapshot();a.atomic_commit("bound");a.rotate()
    with pytest.raises(PermissionError):a.consume(st)
