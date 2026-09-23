# 026 — T22 Real-Path Integration Plan

## Objective

Move the T21 correlation relation into the real cMCP call path without changing cMCP production code.

Target path:

CMCPProxy.call_tool()
→ existing cMCP authorization/gateway checks
→ EABC disposable adapter
→ commit-to-call verification
→ real _forward_to_upstream()
→ mock MCP server
→ cMCP terminal evidence

## Design

The adapter is a test-only wrapper around the forwarding seam.

It must:

1. receive the cMCP call_id, tool_name and arguments;
2. obtain the cMCP request_payload_hash from the call-path artifact;
3. verify the EABC commit;
4. verify commit.call_id == cMCP call_id;
5. verify commit.tool_name == tool_name;
6. verify commit.request_payload_hash == hash(arguments);
7. permit the real forwarding method only after all checks pass;
8. expose commit_id for evidence correlation.

## Success criteria

### Positive

A valid commit reaches the mock upstream server with byte-equivalent canonical arguments.

### Negative

No commit, wrong call, wrong tool or wrong request digest produces no upstream invocation.

## Evidence

The test should emit JSON containing:

- cMCP revision;
- test id;
- commit_id;
- call_id;
- request_payload_hash;
- forwarding result;
- effect count;
- terminal AuditEntry hash.

The evidence should make clear which assertions are adapter-level and which are observed from the real cMCP path.

## Non-goals

- no modification of Cedar;
- no modification of TEE verification;
- no replacement of GatewayClaim or TRACE;
- no claim that the resulting adapter is already part of AgenTrust;
- no claim of physical enforcement.

## Decision point

If T22 succeeds, freeze the technical experiment and prepare a concise collaboration artifact. If it exposes a real incompatibility, document that incompatibility precisely and use it to refine the profile rather than adding more abstractions.
