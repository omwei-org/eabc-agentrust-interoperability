# 022 — T18 Forwarding Seam

## Result

T18 models the exact semantic seam identified in cMCP v0.5.0:

`Cedar / native gateway admission → _forward_to_upstream(..., arguments)`

The experiment places an EABC commit gate immediately at that seam.

## Invariants tested

- no commit → no forwarding;
- request digest mismatch → no forwarding;
- execution identity mismatch → no forwarding;
- valid commit + exact arguments → forwarding;
- the arguments reaching the forwarding seam hash to the committed digest.

All of these are adapter-level tests. They do not claim that upstream cMCP v0.5.0 currently contains this EABC gate.

## Why this matters for collaboration

The seam is narrow enough that an EABC profile could be experimentally integrated without replacing:

- Cedar authorization;
- cMCP's native ingress enforcement;
- TEE/hardware attestation;
- AuditEntry;
- GatewayClaim;
- TRACE/SCITT.

The proposed integration is therefore:

`Cedar → native cMCP gateway → EABC commit gate → _forward_to_upstream → effect`

The EABC gate consumes existing cMCP identity/policy/request artifacts and adds an explicit commit relation.

## Important limitation

T18 is not yet a real runtime patch or upstream pull request. The next step is to create a disposable integration branch/fork or test seam that wraps the real cMCP forwarding function and produces machine-readable evidence.

The target is to demonstrate the six cross-artifact invariants against an actual cMCP call, not only against a local model.

## Collaboration proposal

If the real-runtime experiment succeeds, the artifact to share with AgenTrust should be a small interoperability PR or companion profile, not a broad redesign:

**EABC Execution Commit Profile for MCP — experimental integration**

The AgenTrust team can then decide whether the commit semantics are useful for cMCP, TRACE, or a future MCP execution-boundary profile.
