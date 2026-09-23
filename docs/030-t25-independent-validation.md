# 030 — T25 Independent Interoperability Validation

## Objective

Validate the EABC execution-commit hypothesis independently, using only the public cMCP implementation and this repository.

AgenTrust participation is not required for this phase.

## Principle

The experiment must distinguish three things:

1. behavior that exists in upstream cMCP;
2. behavior added by the EABC adapter;
3. behavior that remains outside the demonstrated boundary.

## Target path

cMCP CMCPProxy.call_tool()
→ existing cMCP controls
→ EABC adapter commit gate
→ existing forwarding seam
→ mock MCP effect
→ existing cMCP evidence

## Independent test families

### A. Commit gating

- valid commit → effect;
- missing commit → no effect;
- invalid commit → no effect.

### B. Exact execution binding

- changed arguments → no effect;
- changed tool → no effect;
- changed call_id → no effect;
- changed policy identity → no effect.

### C. Temporal authority

- prepare under epoch N;
- revoke/change authority;
- commit under epoch N;
- expected result: stale/denied and no effect.

### D. Replay

- reuse the same commit;
- expected result depends on the selected EABC replay policy;
- the policy must be explicit and machine-testable.

### E. Evidence correlation

Verify:

EABC commit_id → cMCP call_id → request_payload_hash → terminal evidence reference.

### F. Failure semantics

Every rejected commit must produce an explicit non-effect result and machine-readable reason.

## Evidence standard

Each test run should record:

- exact upstream revision;
- local repository revision;
- test identifier;
- input request digest;
- commit identifier;
- call identifier;
- policy/configuration identifier;
- decision;
- forwarding count;
- effect count;
- evidence reference;
- final test status.

## Independence boundary

No claim should depend on AgenTrust accepting our interpretation.

The purpose is to arrive at AgenTrust with a reproducible experiment and ask only for validation of the resulting interoperability profile.

## Exit criterion

T25 is complete when the core positive, negative, temporal, replay and evidence-correlation tests have machine-readable results in CI.

After that, technical exploration is frozen unless a result exposes a concrete interoperability question.
