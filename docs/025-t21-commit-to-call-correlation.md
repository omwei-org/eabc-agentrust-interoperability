# 025 — T21 Commit-to-Call Correlation

## Objective

T21 replaces the rejected caller-supplied cMCP execution identifier with the identifiers cMCP already exposes.

The experimental relation is:

EABC commit_id → cMCP call_id → AuditEntry.entry_hash

The commit is additionally bound to:

- tool_name
- request_payload_hash
- policy_bundle_hash

## Result

A valid commit binds to the expected cMCP call and terminal evidence reference.

The following mismatches are rejected:

- call_id;
- tool_name;
- request_payload_hash;
- policy_bundle_hash.

## Why this matters

This avoids requiring any new execution_id API in cMCP.

The interoperability profile can therefore remain an external adapter/profile and use existing cMCP correlation primitives.

## Important scope

T21 is still an adapter-level test. It proves the correlation relation, not that current cMCP production forwarding is conditioned on the relation.

The next step is T22: introduce the correlation gate into the real CMCPProxy.call_tool() execution path in a disposable integration layer and verify effect/no-effect against a mock upstream server.

## Collaboration proposition

The proposed AgenTrust collaboration is now narrow:

**Use existing cMCP call/evidence identifiers and add an explicit EABC commit relation at the forwarding seam.**

No replacement of Cedar, TEE enforcement, AuditEntry, GatewayClaim or TRACE is required by the experiment.
