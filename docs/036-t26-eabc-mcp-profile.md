# T26 — EABC Profile for MCP/cMCP

## Status

**Draft profile derived from T25 evidence**

This profile defines how the EABC execution-boundary contract can be instantiated for MCP tool execution through a cMCP-style forwarding gateway.

It does not claim that cMCP v0.5.0 natively implements EABC.

## Normative requirements

### MCP-EABC-001 — Exact request binding — MUST

The execution commit MUST bind to the exact MCP execution tuple:

- call_id
- tool_name
- request_payload_hash
- applicable policy/configuration identity

A mismatch MUST prevent forwarding.

Evidence: T25.6.

### MCP-EABC-002 — Commit gate — MUST

Forwarding to the upstream MCP server MUST occur only after a valid EABC COMMIT has been established.

Evidence: T25.2, T25.4.

### MCP-EABC-003 — Single-use commit — MUST

An EABC COMMIT MUST NOT authorize more than one execution attempt unless the profile explicitly defines an idempotent/retry semantic.

Evidence: T25.5.

### MCP-EABC-004 — Failure-state preservation — MUST

The profile MUST distinguish at least:

- no transport started;
- transport may have started / outcome unknown;
- response received;
- terminal evidence durable.

Evidence: T25.4.

### MCP-EABC-005 — Durable binding evidence — MUST

The profile MUST provide durable evidence linking:

`commit_id → call_id → tool_name → request_payload_hash → policy/configuration identity → terminal audit reference`

Evidence: T25.7.

### MCP-EABC-006 — Native/adapter boundary declaration — MUST

Implementations MUST explicitly identify which EABC properties are native to the MCP gateway and which are supplied by an adapter.

Evidence: T25.8.

### MCP-EABC-007 — Complete mediation — MUST be scoped

An implementation MUST state the effect domain over which its forwarding boundary is exclusive.

A gateway MUST NOT claim universal effect mediation merely because it mediates MCP traffic.

Evidence: T25.9.

### MCP-EABC-008 — Evidence is not physical truth — MUST

Terminal audit, signatures, or hashes MUST NOT be represented as proof that an external physical-world effect occurred unless independently grounded evidence establishes that fact.

Evidence: T25.9.

## Recommended requirements

### MCP-EABC-101 — Independent authority

Implementations SHOULD maintain an authority object or equivalent authorization snapshot that is independently identifiable at COMMIT time.

### MCP-EABC-102 — Explicit final authority check

Implementations SHOULD expose a distinct final-authority operation immediately before COMMIT.

### MCP-EABC-103 — Execution evidence

Implementations SHOULD expose an explicit execution-attestation/evidence reference rather than requiring verifiers to reconstruct it solely from audit entries.

## Non-goals

This profile does not define:

- Cedar policy syntax;
- MCP transport semantics;
- TEE attestation formats;
- physical robot safety;
- universal authorization policy;
- downstream physical effect verification.

## Profile result

T25 supports a **profile candidate**, not a claim of native EABC implementation.

The central invariant is:

**MAY → COMMIT → DID**

with COMMIT bound to the exact MCP execution object.
