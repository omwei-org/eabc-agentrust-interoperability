from __future__ import annotations
import hashlib, json, urllib.request
from harness.mock_mcp_server import CaptureServer

def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

def test_t03_transport_capture_binds_exact_request():
    server=CaptureServer(); server.start()
    try:
        authorized={"jsonrpc":"2.0","id":"cmd-t03-transport","method":"tools/call","params":{"name":"test.echo","arguments":{"amount":7,"destination":"cell-3","mode":"move"}}}
        body=canonical(authorized)
        req=urllib.request.Request(server.url,data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=3) as response: assert response.status==200
        received=server.captured[0]["payload"]
        assert received==authorized
        assert server.captured[0]["sha256"]==hashlib.sha256(body).hexdigest()
    finally: server.stop()
