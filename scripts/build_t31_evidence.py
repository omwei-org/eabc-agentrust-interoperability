from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

PIN = "f8743e013786b094caaa70c336519834e73c74d5"
UPSTREAM = Path("upstream/cmcp")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_info(relative: str) -> dict:
    path = UPSTREAM / relative
    data = path.read_bytes()
    text = data.decode("utf-8")
    return {
        "path": relative,
        "sha256": sha256_bytes(data),
        "bytes": len(data),
        "lines": len(text.splitlines()),
    }


def class_method_lines(source: str, class_name: str, method_name: str) -> tuple[int, int]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)) and child.name == method_name:
                    return child.lineno, child.end_lineno
    raise RuntimeError(f"{class_name}.{method_name} not found")


def await_attr_calls(source: str, class_name: str, attr_name: str) -> list[int]:
    tree = ast.parse(source)
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return [
        node.lineno
        for node in ast.walk(cls)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == attr_name
    ]


def main() -> None:
    root = Path("evidence/t30-3/t31")
    root.mkdir(parents=True, exist_ok=True)

    proxy_source = (UPSTREAM / "src/cmcp_runtime/mcp/proxy.py").read_text(encoding="utf-8")
    server_source = (UPSTREAM / "src/cmcp_runtime/mcp/server.py").read_text(encoding="utf-8")

    # Derive the production ingress facts from the pristine pinned AST rather
    # than recording the conclusion as an unchecked constant.
    server_tree = ast.parse(server_source)
    server_class = next(
        node for node in server_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "MCPServer"
    )
    mcp_route = next(
        node for node in server_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    route_text = ast.get_source_segment(server_source, mcp_route) or ""
    has_mcp_post_route = 'Route("/mcp", self._handle_mcp, methods=["POST"])' in route_text
    handle_mcp = next(node for node in server_class.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "_handle_mcp")
    handle_tool = next(node for node in server_class.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "_handle_tool_call")
    call_tool_awaits = [
        node for node in ast.walk(handle_tool)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "call_tool"
    ]
    handle_tool_dispatches = [
        node for node in ast.walk(handle_mcp)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "_handle_tool_call"
    ]

    call_tool_lines = class_method_lines(proxy_source, "CMCPProxy", "call_tool")
    forward_lines = class_method_lines(proxy_source, "CMCPProxy", "_forward_to_upstream")
    forward_call_sites = await_attr_calls(proxy_source, "CMCPProxy", "_forward_to_upstream")

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
        "ingress_source_locations": {
            "MCPServer.__init__": {"start_line": mcp_route.lineno, "end_line": mcp_route.end_lineno},
            "MCPServer._handle_mcp": {"start_line": handle_mcp.lineno, "end_line": handle_mcp.end_lineno},
            "MCPServer._handle_tool_call": {"start_line": handle_tool.lineno, "end_line": handle_tool.end_lineno},
            "await _handle_tool_call sites": [n.lineno for n in handle_tool_dispatches],
            "await proxy.call_tool sites": [n.lineno for n in call_tool_awaits],
        },
        "ingress_ast_checks": {
            "post_mcp_route": has_mcp_post_route,
            "tools_call_dispatch": bool(handle_tool_dispatches),
            "single_proxy_call_tool_in_handle": len(call_tool_awaits) == 1,
        },
        "source_files": [
            source_info("src/cmcp_runtime/mcp/server.py"),
            source_info("src/cmcp_runtime/mcp/proxy.py"),
        ],
        "source_locations": {
            "CMCPProxy.call_tool": {"start_line": call_tool_lines[0], "end_line": call_tool_lines[1]},
            "CMCPProxy._forward_to_upstream": {"start_line": forward_lines[0], "end_line": forward_lines[1]},
            "await _forward_to_upstream call_sites": forward_call_sites,
        },
        "alternate_production_ingress_identified": not (
            has_mcp_post_route
            and bool(handle_tool_dispatches)
            and len(call_tool_awaits) == 1
            and len(forward_call_sites) == 1
        ),
        "claim_scope": "inspected pinned runtime surface",
        "methodology": "AST/source inspection of pristine pinned checkout before disposable T30.3 patch",
    }

    payload = json.dumps(record, sort_keys=True, indent=2) + "\n"
    (root / "ingress-inventory.json").write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload.encode()).hexdigest()
    (root / "ingress-inventory.sha256").write_text(
        f"{digest}  ingress-inventory.json\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
