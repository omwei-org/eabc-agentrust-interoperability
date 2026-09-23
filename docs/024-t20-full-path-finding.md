# 024 — T20 Full-Path Finding

## Critical source finding

Inspection of cMCP v0.5.0 shows that CMCPProxy.call_tool() enters _call_tool_impl(), where request hashing occurs first.

However, the current implementation explicitly refuses a supplied execution_id through _check_execution_available() with rule execution:unavailable and deny reason execution_correlation_unavailable.

The source comment states that execution correlation remains unavailable until action binding and atomic terminal/audit persistence contracts are implemented.

## Consequence for EABC interoperability

This changes the immediate integration strategy.

The previously proposed profile field execution_id can map to an existing cMCP artifact only when cMCP is operating on its normal internally generated/correlated call path. A caller-supplied EABC execution identifier cannot currently be passed through call_tool() as an active execution correlation value.

Therefore:

- request_payload_hash remains directly usable;
- tool_name remains directly usable;
- policy identity remains profile-mappable;
- AuditEntry evidence remains usable;
- an EABC commit_id remains an adapter-level addition;
- caller-supplied execution_id is currently a cMCP integration constraint, not a demonstrated interoperability field.

## Important correction

T19 should not be interpreted as proof that a caller-supplied EABC execution_id can already traverse the full cMCP runtime.

The real full-path experiment must preserve cMCP's existing execution-correlation behavior and introduce EABC correlation at the adapter/forwarding seam without relying on the rejected execution_id argument.

## Revised integration shape

CMCPProxy.call_tool()
→ existing cMCP authorization and gateway checks
→ EABC adapter/commit gate
→ _forward_to_upstream()
→ effect
→ cMCP AuditEntry
→ GatewayClaim / TRACE

The adapter may maintain its own commit_id and correlate it with the cMCP call_id and terminal AuditEntry.entry_hash.

## Collaboration significance

This is actually a cleaner collaboration boundary.

AgenTrust does not need to adopt an EABC execution-id primitive first. EABC can experimentally bind its commit to cMCP's existing call correlation:

EABC commit_id → cMCP call_id → AuditEntry.entry_hash → GatewayClaim

The next experiment should therefore test commit-to-call correlation, not force an execution_id through cMCP's currently refused execution API.
