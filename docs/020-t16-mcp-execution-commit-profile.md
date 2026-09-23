# 020 — EABC Execution Commit Profile for MCP

## Status

Experimental interoperability profile. Not an AgenTrust or EABC normative specification.

## Purpose

Define the smallest semantic contract that can connect existing AgenTrust/cMCP authorization and evidence artifacts to an explicit EABC execution commit.

The profile intentionally does not replace Cedar, cMCP enforcement, GatewayClaim, TRACE, or SCITT.

## Commit object

A profile implementation SHOULD bind:

- `commit_id`: unique commit identifier;
- `execution_id`: cMCP execution correlation identifier;
- `request_payload_hash`: SHA-256 of canonical tool arguments using the cMCP convention;
- `policy_bundle_hash`: identity of the policy material used for authorization;
- `authority_version`: profile-defined freshness/version value;
- `tool_name`: MCP tool identity;
- `effect_target_id`: execution-domain target identity where available.

The exact representation is experimental.

## Required invariants

### I1 — Authorization precedes commit

No EABC commit exists without a successful applicable authorization decision.

### I2 — Exact argument binding

The commit's `request_payload_hash` MUST equal the digest calculated from the arguments presented at the effect seam.

### I3 — Policy binding

The commit MUST identify the policy material against which the authorization was evaluated.

### I4 — Freshness

A prepared commit MUST be rejected when its authority or policy freshness value no longer matches the active value.

### I5 — Single-use commit

A consumed `commit_id` MUST NOT authorize a second effect unless the profile explicitly defines replay semantics.

### I6 — Evidence linkage

The terminal cMCP AuditEntry SHOULD contain a reference to the commit, directly or through an interoperable correlation field.

### I7 — Evidence continuity

The commit reference SHOULD be included in the evidence chain so that GatewayClaim/TRACE can expose the relation without exposing sensitive arguments.

## Minimal message flow

```
MCP request
  ↓
cMCP identity + Cedar authorization
  ↓
EABC PREPARE
  ↓
freshness / final authority check
  ↓
EABC COMMIT
  ↓
cMCP forwarding gate
  ↓
MCP effect
  ↓
AuditEntry
  ↓
GatewayClaim / TRACE
```

## What this profile does NOT claim

It does not claim that current cMCP v0.5.0 already implements `commit_id`, `authority_version`, or all of these invariants.

It also does not claim that an EABC adapter is required for every MCP deployment.

The purpose is to make a testable interoperability hypothesis.

## Collaboration hypothesis

The strongest joint experiment is:

**Can an EABC commit adapter consume existing cMCP artifacts and add only the missing commit semantics, while preserving cMCP authorization, TEE enforcement, and AgenTrust evidence?**

Success would be measured by cross-artifact invariants, not by adopting either project's terminology wholesale.

## Next

T17 should implement this profile against the synthetic adapter and then replay it against captured/fixture cMCP AuditEntry and GatewayClaim artifacts. The objective is to prove that the profile adds a commit relation without duplicating evidence or policy evaluation.
