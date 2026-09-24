# T31 — cMCP forwarding ingress enumeration

## Purpose

T31 inspects the pinned cMCP runtime revision used by T30.3:

- repository: \`agentrust-io/cmcp\`
- revision: \`f8743e013786b094caaa70c336519834e73c74d5\`

The declared consequence under test is deliberately narrow:

> the requested MCP tool invocation reaches the configured upstream MCP server.

This is a source-level complete-mediation inventory. It is not a claim of native cMCP EABC conformance.

## Result

Within the inspected production runtime surface, the upstream tool-invocation consequence has one production forwarding call site:

    MCPServer._handle_mcp()
      -> _handle_tool_call()
      -> CMCPProxy.call_tool()
      -> CMCPProxy._forward_to_upstream()
      -> HTTP POST to catalog server.url
           OR
         StdioServer.call() for a catalog stdio server

The pinned CMCPProxy.call_tool() contains the single transition from the native pre-forwarding gateway stage to _forward_to_upstream():

    Step 5a: native pre-call interception
            |
            v
    Step 5b: forward to the attested upstream MCP server
            |
            +--> _forward_to_upstream()
                  +--> network HTTP POST
                  +--> stdio child call

T30.3 inserts its disposable EABC hook immediately before this Step 5b transition. Therefore the experiment covers both forwarding implementations reached through this call site.

## Ingress inventory

### 1. HTTP MCP endpoint — tools/call

Production route:

    POST /mcp
      -> MCPServer._handle_mcp()
      -> MCPServer._handle_tool_call()
      -> CMCPProxy.call_tool()

This is the production-reachable tool-call ingress and the path exercised by T30.3.

### 2. /tools/list

    GET /tools/list

This route exposes catalog/tool discovery information. It does not invoke a configured tool and therefore does not produce the declared consequence "tool invocation reaches upstream".

The proxy's internal discovery path may contact an upstream server with tools/list, including through HTTP or stdio, but that is discovery/provenance traffic, not the declared tool-effect consequence. It must not be conflated with tool execution forwarding.

### 3. Session/control routes

The inspected server routes include:

- health/readiness;
- trace-claim retrieval;
- audit export;
- session reset;
- session close;
- catalog exception;
- kill-switch trip/unblock.

These routes do not contain an alternate production path to the upstream tool-invocation consequence.

### 4. Direct proxy forwarding call sites

A repository-wide search for _forward_to_upstream at the pinned revision identifies the production definition and its production invocation in src/cmcp_runtime/mcp/proxy.py. Other matches are benchmark/test seams that replace or call the private method directly; those are not production ingress paths.

This distinction is important: directly invoking the private forwarding helper is not evidence of a production bypass.

### 5. Upstream transport branches

The forwarding helper has two transport branches:

- network upstream: httpx.AsyncClient.post(entry.server.url, ...);
- stdio upstream: StdioServer.call(...).

Both are reached from the same call_tool() -> _forward_to_upstream() transition. T30.3's hook is therefore above the transport split rather than only above the HTTP branch.

## Mediation conclusion

For the inspected pinned runtime surface:

> No alternate production-reachable ingress to the declared tool-invocation consequence was identified outside call_tool() -> _forward_to_upstream().

This is an inspection result, not a universal proof of complete mediation.

The precise experimental claim supported by T30.3 + T31 is:

> The EABC hook is positioned at the common production forwarding transition for the inspected cMCP tool-call runtime surface, covering both configured HTTP and stdio upstream transport branches.

It does not establish:

- native cMCP EABC support;
- hardware bypass resistance;
- physical-effect mediation;
- exactly-once external execution;
- mediation of future transports or code paths not present at the pinned revision;
- protection against a compromised runtime outside the stated threat model.

## Evidence discipline

The source inventory must remain pinned to:

f8743e013786b094caaa70c336519834e73c74d5

Future cMCP revisions must trigger a fresh ingress inventory. A newly introduced transport, endpoint, direct upstream client, or alternate invocation path can invalidate this source-level conclusion even if the existing T30.3 tests remain green.
