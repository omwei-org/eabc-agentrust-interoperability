"""T36 authority-state provenance experiment with real Ed25519 verification."""
import asyncio
import base64
import hashlib
import json
import threading
import time
from dataclasses import dataclass, replace
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


class AuthorityIssuer:
    def __init__(self, issuer="issuer-t36", key_id="key-t36"):
        self.issuer = issuer
        self.key_id = key_id
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key()

    def state(self, epoch, *, authority_ref="authority-t36", state_digest=None,
              issued_at=None, valid_from=None, valid_until=None):
        now = int(time.time()) if issued_at is None else issued_at
        vf = now if valid_from is None else valid_from
        vu = now + 3600 if valid_until is None else valid_until
        digest = state_digest or "sha256:" + hashlib.sha256(
            f"{authority_ref}:{epoch}".encode()).hexdigest()
        unsigned = {
            "authority_ref": authority_ref,
            "authority_epoch": epoch,
            "state_digest": digest,
            "issuer": self.issuer,
            "issued_at": now,
            "valid_from": vf,
            "valid_until": vu,
            "key_id": self.key_id,
            "algorithm": "Ed25519",
        }
        sig = self.private.sign(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode())
        return AuthorityState(**unsigned, signature=base64.b64encode(sig).decode())

    def public_b64(self):
        return base64.b64encode(
            self.public.public_bytes(Encoding.Raw, PublicFormat.Raw)
        ).decode()


class AuthorityVerifier:
    def __init__(self, trusted, allowed_refs):
        self.trusted = trusted
        self.allowed_refs = set(allowed_refs)

    def verify(self, state, now, current_epoch):
        if state.authority_ref not in self.allowed_refs:
            raise PermissionError("EABC_UNKNOWN_AUTHORITY_REF")
        if state.issuer not in self.trusted or state.key_id not in self.trusted[state.issuer]:
            raise PermissionError("EABC_UNTRUSTED_ISSUER")
        if state.algorithm != "Ed25519":
            raise PermissionError("EABC_UNSUPPORTED_AUTHORITY_ALGORITHM")
        if not state.valid_from <= now <= state.valid_until:
            raise PermissionError("EABC_AUTHORITY_STATE_EXPIRED")
        unsigned = {
            "authority_ref": state.authority_ref,
            "authority_epoch": state.authority_epoch,
            "state_digest": state.state_digest,
            "issuer": state.issuer,
            "issued_at": state.issued_at,
            "valid_from": state.valid_from,
            "valid_until": state.valid_until,
            "key_id": state.key_id,
            "algorithm": state.algorithm,
        }
        key = self.trusted[state.issuer][state.key_id]
        try:
            key.verify(base64.b64decode(state.signature), json.dumps(
                unsigned, sort_keys=True, separators=(",", ":")).encode())
        except Exception as exc:
            raise PermissionError("EABC_AUTHORITY_SIGNATURE_INVALID") from exc
        if state.authority_epoch != current_epoch:
            raise PermissionError("EABC_AUTHORITY_EPOCH_MISMATCH")
        return True


def _sink(path):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            n=int(self.headers.get("Content-Length","0")); self.rfile.read(n)
            body=b'{"jsonrpc":"2.0","id":1,"result":{"ok":true}}'
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
        server=ServerIdentity(display_name="T36 Sink",url=url,
            tls_fingerprint="SHA256:"+"A"*43+"=",spiffe_id=None,
            transport="http-sse",rotation_mode="key-pinned"),
        approved_definition=ApprovedDefinition(description="effect",
            input_schema={"type":"object"},output_schema=None),
        definition_hash="sha256:"+"0"*64,compliance_domain="public",
        requires_baa=False,sensitivity_level="public",
        added_at="2026-09-25T00:00:00Z",approved_by="t36")
    catalog=ToolCatalog(entries={"test.effect":entry},catalog_hash="sha256:"+"1"*64)
    config=Config(attestation=AttestationConfig(enforcement_mode=EnforcementMode.ENFORCING))
    with patch("cmcp_runtime.mcp.proxy.MCPGateway"),patch("cmcp_runtime.mcp.proxy.MCPResponseScanner"):
        p=CMCPProxy(catalog=catalog,policy_evaluator=MagicMock(),
            session=SessionState(session_id="t36-agent"),
            audit_chain=AuditChain("t36"),config=config)
    p._check_health=MagicMock(return_value=None)
    p._check_upstream_drift=AsyncMock(return_value=False)
    p._policy.evaluate.return_value=MagicMock(rule_matched="test.allow",would_have_denied=False,advice={})
    p._mcp_gateway.intercept_tool_call.return_value=(True,"")
    p._mcp_gateway.intercept_tool_response.return_value=MagicMock(threats=[],content=None,allowed=True)
    p._policy.authorize_egress.return_value=MagicMock(would_have_denied=False)
    return p


def _commit(p, state, eid, cid, args, mid):
    tool="test.effect"; policy="t36-policy"; digest=request_digest(tool,args)
    return EABCCommit(commit_id=mid,call_id=cid,tool_name=tool,
        request_payload_hash=digest,policy_id=policy,
        agent_identity=p._session.session_id,execution_id=eid,
        action_binding=action_binding_digest(agent_identity=p._session.session_id,
            execution_id=eid,tool_name=tool,request_payload_hash=digest,policy_id=policy),
        authority_ref=state.authority_ref,authority_epoch=state.authority_epoch)


async def invoke(p,cid,args,eid):
    return await p.call_tool(cid,"test.effect",args,execution_id=eid)


def instrument(p,c):
    original=p._forward_to_upstream
    async def wrapped(*a,**kw):
        c["forwarding"]+=1
        return await original(*a,**kw)
    p._forward_to_upstream=wrapped


def setup(p,state,verifier,commit):
    p._t36_state=state
    p._t36_verifier=verifier
    p._t36_commit=commit
    p._t36_adapter=EABCMCPAdapter()
    p._t36_policy_id="t36-policy"


def trusted(issuer):
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    return {issuer.issuer: {issuer.key_id: issuer.public}}


@pytest.mark.asyncio
async def test_t36_a_valid_provenance_fresh_epoch(tmp_path):
    s,url=_sink(tmp_path/"a"); i=AuthorityIssuer(); state=i.state(1); v=AuthorityVerifier(trusted(i),["authority-t36"])
    try:
        p=_proxy(url); setup(p,state,v,_commit(p,state,"e-a","c-a",{"v":1},"m-a")); c={"forwarding":0}; instrument(p,c)
        r=await invoke(p,"c-a",{"v":1},"e-a"); assert r.allowed is True and c["forwarding"]==1
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t36_b_untrusted_issuer(tmp_path):
    s,url=_sink(tmp_path/"b"); i=AuthorityIssuer(); state=i.state(1); v=AuthorityVerifier({},["authority-t36"])
    try:
        p=_proxy(url); setup(p,state,v,_commit(p,state,"e-b","c-b",{"v":2},"m-b")); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_UNTRUSTED_ISSUER"): await invoke(p,"c-b",{"v":2},"e-b")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t36_c_modified_epoch_breaks_signature(tmp_path):
    s,url=_sink(tmp_path/"c"); i=AuthorityIssuer(); state=i.state(1); tampered=replace(state,authority_epoch=2); v=AuthorityVerifier(trusted(i),["authority-t36"])
    try:
        p=_proxy(url); setup(p,tampered,v,_commit(p,tampered,"e-c","c-c",{"v":3},"m-c")); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_SIGNATURE_INVALID"): await invoke(p,"c-c",{"v":3},"e-c")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t36_d_modified_digest_breaks_signature(tmp_path):
    s,url=_sink(tmp_path/"d"); i=AuthorityIssuer(); state=i.state(1); tampered=replace(state,state_digest="sha256:forged"); v=AuthorityVerifier(trusted(i),["authority-t36"])
    try:
        p=_proxy(url); setup(p,tampered,v,_commit(p,tampered,"e-d","c-d",{"v":4},"m-d")); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_SIGNATURE_INVALID"): await invoke(p,"c-d",{"v":4},"e-d")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t36_e_signed_but_stale(tmp_path):
    s,url=_sink(tmp_path/"e"); i=AuthorityIssuer(); old=i.state(1); v=AuthorityVerifier(trusted(i),["authority-t36"])
    try:
        p=_proxy(url); setup(p,old,v,_commit(p,old,"e-e","c-e",{"v":5},"m-e")); p._t36_current_epoch=2; c={"forwarding":0}; instrument(p,c)
        original=p._t36_verifier.verify
        p._t36_verifier.verify=lambda st,now,current_epoch: original(st,now,2)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_EPOCH_MISMATCH"): await invoke(p,"c-e",{"v":5},"e-e")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t36_f_unknown_authority_ref(tmp_path):
    s,url=_sink(tmp_path/"f"); i=AuthorityIssuer(); state=i.state(1,authority_ref="unknown"); v=AuthorityVerifier(trusted(i),["authority-t36"])
    try:
        p=_proxy(url); setup(p,state,v,_commit(p,state,"e-f","c-f",{"v":6},"m-f")); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_UNKNOWN_AUTHORITY_REF"): await invoke(p,"c-f",{"v":6},"e-f")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t36_g_valid_new_epoch(tmp_path):
    s,url=_sink(tmp_path/"g"); i=AuthorityIssuer(); state=i.state(2); v=AuthorityVerifier(trusted(i),["authority-t36"])
    try:
        p=_proxy(url); setup(p,state,v,_commit(p,state,"e-g","c-g",{"v":7},"m-g")); c={"forwarding":0}; instrument(p,c)
        r=await invoke(p,"c-g",{"v":7},"e-g"); assert r.allowed is True and c["forwarding"]==1
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t36_h_replayed_old_signed_state(tmp_path):
    s,url=_sink(tmp_path/"h"); i=AuthorityIssuer(); old=i.state(1); v=AuthorityVerifier(trusted(i),["authority-t36"])
    try:
        p=_proxy(url); setup(p,old,v,_commit(p,old,"e-h","c-h",{"v":8},"m-h")); c={"forwarding":0}; instrument(p,c)
        original=p._t36_verifier.verify
        p._t36_verifier.verify=lambda st,now,current_epoch: original(st,now,2)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_EPOCH_MISMATCH"): await invoke(p,"c-h",{"v":8},"e-h")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t36_i_expired_window(tmp_path):
    s,url=_sink(tmp_path/"i"); i=AuthorityIssuer(); now=int(time.time()); state=i.state(1,issued_at=now-100,valid_from=now-100,valid_until=now-1); v=AuthorityVerifier(trusted(i),["authority-t36"])
    try:
        p=_proxy(url); setup(p,state,v,_commit(p,state,"e-i","c-i",{"v":9},"m-i")); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_AUTHORITY_STATE_EXPIRED"): await invoke(p,"c-i",{"v":9},"e-i")
        assert c["forwarding"]==0
    finally:s.shutdown()


@pytest.mark.asyncio
async def test_t36_j_revoked_issuer(tmp_path):
    s,url=_sink(tmp_path/"j"); i=AuthorityIssuer(); state=i.state(1); v=AuthorityVerifier(trusted(i),["authority-t36"]); v.trusted[i.issuer]={}
    try:
        p=_proxy(url); setup(p,state,v,_commit(p,state,"e-j","c-j",{"v":10},"m-j")); c={"forwarding":0}; instrument(p,c)
        with pytest.raises(PermissionError,match="EABC_UNTRUSTED_ISSUER"): await invoke(p,"c-j",{"v":10},"e-j")
        assert c["forwarding"]==0
    finally:s.shutdown()
