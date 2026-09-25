"""T37 authority-key lifecycle / trust-transition experiment."""
import asyncio, base64, hashlib, json, threading, time
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from eabc_profile import EABCCommit, EABCMCPAdapter
from eabc_profile.adapter import action_binding_digest, request_digest
from cmcp_runtime.audit.chain import AuditChain
from cmcp_runtime.catalog.loader import ApprovedDefinition, CatalogEntry, ServerIdentity, ToolCatalog
from cmcp_runtime.config import AttestationConfig, Config, EnforcementMode
from cmcp_runtime.session.state import SessionState


@dataclass(frozen=True)
class AuthorityState:
    authority_ref: str
    authority_epoch: int
    state_digest: str
    issuer: str
    issued_at: int
    valid_from: int
    valid_until: int
    key_id: str
    algorithm: str
    signature: str


class KeyAuthority:
    def __init__(self):
        self.issuers = {}
        self.trusted = {}
        self.lock = threading.Lock()

    def add_key(self, issuer, key_id):
        key = Ed25519PrivateKey.generate()
        self.issuers[(issuer, key_id)] = key
        return key

    def trust(self, issuer, key_id):
        with self.lock:
            self.trusted.setdefault(issuer, set()).add(key_id)

    def revoke(self, issuer, key_id):
        with self.lock:
            self.trusted.setdefault(issuer, set()).discard(key_id)

    def snapshot(self):
        with self.lock:
            return {issuer: set(keys) for issuer, keys in self.trusted.items()}

    def state(self, issuer, key_id, epoch, *, authority_ref="authority-t37",
              valid_until=None):
        now=int(time.time())
        key=self.issuers[(issuer,key_id)]
        unsigned={
            "authority_ref":authority_ref,"authority_epoch":epoch,
            "state_digest":"sha256:"+hashlib.sha256(f"{authority_ref}:{epoch}".encode()).hexdigest(),
            "issuer":issuer,"issued_at":now,"valid_from":now,
            "valid_until":now+3600 if valid_until is None else valid_until,
            "key_id":key_id,"algorithm":"Ed25519",
        }
        sig=key.sign(json.dumps(unsigned,sort_keys=True,separators=(",",":")).encode())
        return AuthorityState(**unsigned,signature=base64.b64encode(sig).decode())

    def verify(self,state,now,current_epoch,after_verify=None):
        with self.lock:
            trusted=set(self.trusted.get(state.issuer,set()))
        if state.authority_ref!="authority-t37": raise PermissionError("EABC_UNKNOWN_AUTHORITY_REF")
        if state.key_id not in trusted: raise PermissionError("EABC_KEY_NOT_TRUSTED")
        key=self.issuers.get((state.issuer,state.key_id))
        if key is None: raise PermissionError("EABC_UNKNOWN_KEY")
        public=key.public_key()
        unsigned={k:getattr(state,k) for k in (
            "authority_ref","authority_epoch","state_digest","issuer",
            "issued_at","valid_from","valid_until","key_id","algorithm")}
        try:
            public.verify(base64.b64decode(state.signature),
                json.dumps(unsigned,sort_keys=True,separators=(",",":")).encode())
        except Exception as exc:
            raise PermissionError("EABC_AUTHORITY_SIGNATURE_INVALID") from exc
        if after_verify is not None: after_verify()
        with self.lock:
            if state.key_id not in self.trusted.get(state.issuer,set()):
                raise PermissionError("EABC_KEY_NOT_TRUSTED")
        if not state.valid_from <= now <= state.valid_until:
            raise PermissionError("EABC_AUTHORITY_STATE_EXPIRED")
        if state.authority_epoch != current_epoch:
            raise PermissionError("EABC_AUTHORITY_EPOCH_MISMATCH")
        return True


def sink(path):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n=int(self.headers.get("Content-Length","0")); self.rfile.read(n)
            b=b'{"jsonrpc":"2.0","id":1,"result":{"ok":true}}'
            self.send_response(200); self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
            path.open("a").write("{\"ok\":true}\n")
        def log_message(self,*_): pass
    s=ThreadingHTTPServer(("127.0.0.1",0),H); threading.Thread(target=s.serve_forever,daemon=True).start()
    return s,f"http://127.0.0.1:{s.server_port}/mcp"


def proxy(url):
    from cmcp_runtime.mcp.proxy import CMCPProxy
    e=CatalogEntry(tool_name="test.effect",server=ServerIdentity(
        display_name="T37 Sink",url=url,tls_fingerprint="SHA256:"+"A"*43+"=",
        spiffe_id=None,transport="http-sse",rotation_mode="key-pinned"),
        approved_definition=ApprovedDefinition(description="effect",input_schema={"type":"object"},output_schema=None),
        definition_hash="sha256:"+"0"*64,compliance_domain="public",requires_baa=False,
        sensitivity_level="public",added_at="2026-09-25T00:00:00Z",approved_by="t37")
    c=ToolCatalog(entries={"test.effect":e},catalog_hash="sha256:"+"1"*64)
    cfg=Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"),patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        p=CMCPProxy(catalog=c,policy_evaluator=MagicMock(),session=SessionState(session_id="t37-agent"),
            audit_chain=AuditChain("t37"),config=cfg)
    p._check_health=MagicMock(return_value=None); p._check_upstream_drift=AsyncMock(return_value=False)
    p._policy.evaluate.return_value=MagicMock(rule_matched="test.allow",would_have_denied=False,advice={})
    p._mcp_gateway.intercept_tool_call.return_value=(True,"")
    p._mcp_gateway.intercept_tool_response.return_value=MagicMock(threats=[],content=None,allowed=True)
    p._policy.authorize_egress.return_value=MagicMock(would_have_denied=False)
    return p


def commit(p,state,eid,cid,mid):
    args={"v":1}; tool="test.effect"; policy="t37-policy"; d=request_digest(tool,args)
    return EABCCommit(commit_id=mid,call_id=cid,tool_name=tool,request_payload_hash=d,policy_id=policy,
        agent_identity=p._session.session_id,execution_id=eid,action_binding=action_binding_digest(
        agent_identity=p._session.session_id,execution_id=eid,tool_name=tool,
        request_payload_hash=d,policy_id=policy),authority_ref=state.authority_ref,
        authority_epoch=state.authority_epoch)


async def invoke(p,cid,eid): return await p.call_tool(cid,"test.effect",{"v":1},execution_id=eid)


def instrument(p,c):
    original=p._forward_to_upstream
    async def wrapped(*a,**kw): c["forwarding"]+=1; return await original(*a,**kw)
    p._forward_to_upstream=wrapped


def setup(p,a,state,cm):
    p._t37_authority=a; p._t37_state=state; p._t37_commit=cm
    p._t37_adapter=EABCMCPAdapter(); p._t37_policy_id="t37-policy"


@pytest.mark.asyncio
async def test_t37_a_key_a_trusted(tmp_path):
    s,u=sink(tmp_path/"a"); a=KeyAuthority(); a.add_key("issuer","A"); a.trust("issuer","A"); st=a.state("issuer","A",1)
    try:
        p=proxy(u); setup(p,a,st,commit(p,st,"e-a","c-a","m-a")); c={"forwarding":0}; instrument(p,c)
        r=await invoke(p,"c-a","e-a"); assert r.allowed and c["forwarding"]==1
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t37_b_revoked_old_state(tmp_path):
    s,u=sink(tmp_path/"b"); a=KeyAuthority(); a.add_key("issuer","A"); a.trust("issuer","A"); st=a.state("issuer","A",1); a.revoke("issuer","A")
    try:
        p=proxy(u); setup(p,a,st,commit(p,st,"e-b","c-b","m-b")); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_KEY_NOT_TRUSTED"): await invoke(p,"c-b","e-b")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t37_c_new_key_not_yet_trusted(tmp_path):
    s,u=sink(tmp_path/"c"); a=KeyAuthority(); a.add_key("issuer","B"); st=a.state("issuer","B",2)
    try:
        p=proxy(u); setup(p,a,st,commit(p,st,"e-c","c-c","m-c")); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_KEY_NOT_TRUSTED"): await invoke(p,"c-c","e-c")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t37_d_new_key_trusted(tmp_path):
    s,u=sink(tmp_path/"d"); a=KeyAuthority(); a.add_key("issuer","B"); a.trust("issuer","B"); st=a.state("issuer","B",2)
    try:
        p=proxy(u); setup(p,a,st,commit(p,st,"e-d","c-d","m-d")); c={"forwarding":0}; instrument(p,c)
        r=await invoke(p,"c-d","e-d"); assert r.allowed and c["forwarding"]==1
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t37_e_old_key_after_rotation(tmp_path):
    s,u=sink(tmp_path/"e"); a=KeyAuthority(); a.add_key("issuer","A"); a.add_key("issuer","B"); a.trust("issuer","A"); old=a.state("issuer","A",1); a.revoke("issuer","A"); a.trust("issuer","B")
    try:
        p=proxy(u); setup(p,a,old,commit(p,old,"e-e","c-e","m-e")); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_KEY_NOT_TRUSTED"): await invoke(p,"c-e","e-e")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t37_f_unknown_key_forgery(tmp_path):
    s,u=sink(tmp_path/"f"); a=KeyAuthority(); a.add_key("issuer","A"); st=a.state("issuer","A",1); a.issuers[("issuer","X")]=Ed25519PrivateKey.generate()
    try:
        p=proxy(u); setup(p,a,st,commit(p,st,"e-f","c-f","m-f")); p._t37_state=AuthorityState(**{**st.__dict__,"key_id":"X","signature":st.signature}); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError): await invoke(p,"c-f","e-f")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t37_g_rotation_race(tmp_path):
    s,u=sink(tmp_path/"g"); a=KeyAuthority(); a.add_key("issuer","A"); a.trust("issuer","A"); st=a.state("issuer","A",1)
    try:
        p=proxy(u); setup(p,a,st,commit(p,st,"e-g","c-g","m-g")); c={"forwarding":0}; instrument(p,c)
        def rotate(): a.revoke("issuer","A")
        with pytest.raises(PermissionError,match="EABC_KEY_NOT_TRUSTED"):
            a.verify(st,int(time.time()),1,after_verify=rotate)
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t37_h_two_boundaries_same_transition(tmp_path):
    s,u=sink(tmp_path/"h"); a=KeyAuthority(); a.add_key("issuer","A"); a.add_key("issuer","B"); a.trust("issuer","A"); a.trust("issuer","B")
    old=a.state("issuer","A",1); new=a.state("issuer","B",2); a.revoke("issuer","A")
    try:
        p1=proxy(u); p2=proxy(u); setup(p1,a,old,commit(p1,old,"e-h1","c-h1","m-h1")); setup(p2,a,new,commit(p2,new,"e-h2","c-h2","m-h2"))
        c1={"forwarding":0}; c2={"forwarding":0}; instrument(p1,c1); instrument(p2,c2)
        r=await asyncio.gather(invoke(p1,"c-h1","e-h1"),invoke(p2,"c-h2","e-h2"),return_exceptions=True)
        assert isinstance(r[0],PermissionError) and getattr(r[1],"allowed",False) and c1["forwarding"]==0 and c2["forwarding"]==1
    finally:s.shutdown()
