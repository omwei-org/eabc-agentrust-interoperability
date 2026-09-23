"""Minimal local HTTP capture server for transport-level evidence."""
from __future__ import annotations
import hashlib, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

class CaptureHandler(BaseHTTPRequestHandler):
    captured = []
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try: payload = json.loads(raw)
        except json.JSONDecodeError: payload = None
        self.__class__.captured.append({"raw": raw, "payload": payload, "sha256": hashlib.sha256(raw).hexdigest()})
        response = json.dumps({"jsonrpc":"2.0","id":payload.get("id") if payload else None,"result":{"content":[{"type":"text","text":"capture-ok"}]}}).encode()
        self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(response))); self.end_headers(); self.wfile.write(response)
    def log_message(self, *_args): return

class CaptureServer:
    def __init__(self):
        CaptureHandler.captured=[]
        self.httpd=ThreadingHTTPServer(("127.0.0.1",0),CaptureHandler)
        self.thread=Thread(target=self.httpd.serve_forever,daemon=True)
    @property
    def url(self): return f"http://127.0.0.1:{self.httpd.server_port}/mcp"
    @property
    def captured(self): return CaptureHandler.captured
    def start(self): self.thread.start()
    def stop(self): self.httpd.shutdown(); self.thread.join(timeout=2)
