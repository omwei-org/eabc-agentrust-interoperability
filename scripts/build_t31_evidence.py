from __future__ import annotations

import hashlib
import json
from pathlib import Path

PIN = "f8743e013786b094caaa70c336519834e73c74d5"


def main() -> None:
    root = Path("evidence/t31")
    root.mkdir(parents=True, exist_ok=True)
    record = {
        "experiment": "T31",
        "upstream_repository": "agentrust-io/cmcp",
        "upstream_commit": PIN,
        "declared_consequence": "MCP tools/call reaches configured upstream",
        "production_ingress": [
            "POST /mcp",
            "MCPServer._handle_mcp",
            "MCPServer._handle_tool_call",
            "CMCPProxy.call_tool",
        ],
        "common_forwarding_transition": "CMCPProxy.call_tool -> _forward_to_upstream",
        "transport_branches": ["http", "stdio"],
        "alternate_production_ingress_identified": False,
        "claim_scope": "inspected pinned runtime surface",
    }
    payload = json.dumps(record, sort_keys=True, indent=2) + "\n"
    (root / "ingress-inventory.json").write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload.encode()).hexdigest()
    (root / "ingress-inventory.sha256").write_text(f"{digest}  ingress-inventory.json\n", encoding="utf-8")


if __name__ == "__main__":
    main()
