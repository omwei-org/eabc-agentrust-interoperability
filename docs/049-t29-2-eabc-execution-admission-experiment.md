# T29.2 — EABC at the cMCP Execution-Admission Boundary

## Status

**Proposed experiment plan — implementation not yet claimed**

T29.1 identified the later cMCP execution-admission path as the cleanest candidate seam for EABC interoperability.

This experiment must be run against that later revision, not silently substituted for the pinned T27/v0.5.0 evidence.

## Boundary under test

```text
authenticated request
  → execution_id / action binding admission
  → cMCP authorization
  → EABC FINAL_AUTHORITY_CHECK
  → EABC COMMIT
  → _forward_to_upstream()
  → MCP upstream consequence
```

The EABC gate is proposed immediately before the transition into the existing upstream forwarding path.

## Exact execution object

The EABC commit should bind, at minimum:

- authenticated agent identity;
- execution_id;
- call_id / attempt identity;
- tool_name;
- request_payload_hash;
- applicable cMCP policy/configuration identity;
- immutable action binding;
- final authority snapshot/reference.

The adapter MUST NOT treat execution_id alone as sufficient authority.

## Required cases

### 1. No EABC COMMIT

A valid cMCP-authorized request with no EABC COMMIT MUST NOT invoke upstream forwarding.

### 2. Exact COMMIT

A fresh COMMIT matching the complete execution object MUST permit exactly one forwarding attempt.

Expected:

```text
MAY → FINAL_AUTHORITY_CHECK → COMMIT → upstream invocation
```

### 3. Substituted request

Changing tool name, arguments, request hash, execution_id, agent identity, policy/configuration identity, or action binding after COMMIT MUST refuse before upstream invocation.

### 4. Replay

Reusing a consumed COMMIT after a terminal outcome MUST refuse before upstream invocation.

A matching execution_id is correlation, not replay permission.

### 5. Concurrent reservation

Two requests attempting to reserve the same authenticated-agent/execution_id with conflicting immutable action bindings MUST produce one authoritative reservation and refuse the conflicting request before upstream invocation.

### 6. Downstream uncertainty

If upstream transport may have started but terminal outcome is unavailable, the system MUST preserve `outcome_unknown`.

It MUST NOT manufacture DID and MUST NOT silently authorize a replay.

## Evidence relation

The experiment should preserve:

```text
EABC commit_id
   → execution_id
   → call_id
   → tool_name
   → request_payload_hash
   → policy/configuration identity
   → terminal audit reference
```

The evidence demonstrates protocol/runtime semantics only. It does not prove an external physical effect.

## Exclusive-mediation test

The decisive EABC property is not that the adapter sits before `_forward_to_upstream()`.

The test must enumerate all production-reachable ingress paths capable of causing the same declared consequence:

**MCP request reaches the configured upstream MCP server.**

For every such path:

```text
consequence ⇒ passed through the controlled COMMIT boundary
```

must hold within the declared effect domain.

Direct invocation of a private Python method is not sufficient evidence of a bypass. Conversely, any production-reachable ingress that can cause the same upstream invocation without the commit boundary is a genuine candidate gap.

## Expected collaboration result

If the experiment succeeds, the resulting profile can state:

- cMCP supplies authenticated identity, attestation, Cedar authorization, action correlation, and audit/TRACE evidence;
- EABC supplies independent execution authority and explicit COMMIT semantics at the declared forwarding boundary;
- the interoperability relation is exact and machine-checkable;
- the exclusive-mediation claim is scoped to MCP-forwarding, not generalized to physical-world effects.

If the experiment fails, the failure should identify which property is missing:

- authority independence;
- exact binding;
- atomic reservation;
- replay handling;
- failure semantics;
- complete mediation;
- or consequence-boundary placement.

## Claim boundary

Even a successful experiment MUST NOT claim:

- native EABC implementation by cMCP;
- hardware-enforced EABC;
- universal mediation outside the declared MCP effect domain;
- proof of a physical-world effect;
- exactly-once physical execution.

The result is an interoperability profile at a declared software execution boundary.
