# 023 — T19 Real cMCP Forwarding Seam

## Finding

The upstream cMCP v0.5.0 test suite exposes a real local HTTP MCP server and directly exercises:

CMCPProxy._forward_to_upstream(call_id, entry, tool_name, arguments)

This confirms that the proposed EABC integration seam is a concrete runtime method, not an abstract architectural box.

T19 adds a test-level gate immediately before that real forwarding seam.

## Result

The valid path reaches the real cMCP forwarding seam with the exact arguments whose digest was committed.

The invalid digest path is rejected by the EABC gate before forwarding is entered.

## What is demonstrated

- cMCP has a directly testable forwarding seam;
- an EABC commit gate can be placed immediately before that seam;
- the gate can bind execution identity, tool identity and request digest;
- the valid path can preserve the exact argument object into forwarding.

## What is not demonstrated

T19 does not modify cMCP's production implementation and therefore does not claim that cMCP v0.5.0 itself enforces EABC commit semantics.

The next experiment should use a disposable subclass/decorator or a small integration branch that wraps the actual CMCPProxy.call_tool() path, rather than invoking _forward_to_upstream() directly.

## Collaboration significance

This is the first point where the collaboration proposal can be stated as an implementation seam:

**AgenTrust owns the governed MCP runtime and evidence path; EABC can experimentally define the commit semantics immediately before cMCP's existing upstream forwarding seam.**

The next step is a full-path test with a mock upstream server:

CMCPProxy.call_tool() → Cedar/gateway checks → EABC commit gate → real _forward_to_upstream() → mock server

That test should produce both effect/no-effect evidence and the final AuditEntry/GatewayClaim correlation.
