# T34 — Revocation / Authority-State Race

## Status

**EXPERIMENTAL TEST PLAN — NOT NATIVE cMCP CONFORMANCE**

T34 tests whether execution authority remains valid across the time window between authorization/admission and the consequence-causing forwarding transition.

T34 is deliberately different from commit substitution or malformed-token testing.

The question is temporal:

> Can a commit created while authority was valid still cause the declared consequence after that authority has been revoked or its state has changed?

## 1. Model

The strict execution-boundary model is:

`AUTHORIZED`
→ `PREPARE / ADMISSION INTENT`
→ **AUTHORITY STATE CHANGE**
→ `FINAL_AUTHORITY_CHECK`
→ `COMMIT`
→ `FORWARD`

or, for an atomic admission implementation:

`AUTHORIZED`
→ `ATOMIC ADMIT + COMMIT`
→ **AUTHORITY STATE CHANGE**
→ `CONSUME / FORWARD`

The experiment MUST make the state transition observable and deterministic. Timing sleeps are not sufficient evidence for the race itself.

## 2. Authority model

T34 introduces an in-memory authority state with:

- `authority_epoch`;
- principal/tool/policy authority validity;
- explicit revocation;
- lock-protected state transitions.

The test harness uses deterministic barriers/events to place revocation at a defined point in the execution sequence.

This is an in-process semantic experiment, not a distributed consensus or exactly-once claim.

## 3. Matrix

| Case | Scenario | Expected forwarding | Expected effect |
|---|---|---:|---:|
| T34-A | Authority stable throughout transaction | 1 | 1 |
| T34-B | Revocation before admission | 0 | 0 |
| T34-C | Revocation after PREPARE, before FINALIZE/COMMIT | 0 | 0 |
| T34-D | Revocation after COMMIT, before forwarding/consume | 0 in Strict | 0 |
| T34-E | Concurrent reuse/race with revocation | ≤1 | ≤1 |
| T34-F | Authority epoch bump without explicit revocation | 0 for stale commit | 0 |

## 4. Decisive observables

T34 records at least:

- `forwarding_entry_count`;
- `eabc_admission_attempts`;
- `eabc_admission_successes`;
- `commit_issued_count`;
- `commit_consumed_count`;
- `authority_epoch_at_issue`;
- `authority_epoch_at_consume`;
- `effect_count`;
- denial reason.

The forwarding seam remains the decisive execution-boundary observable.

## 5. Required strict property

For every commit consumed by the strict execution boundary:

`forwarded ⇒ authority_valid(commit) ∧ commit.authority_epoch = current_authority_epoch`

Therefore:

`commit.authority_epoch != current_authority_epoch ⇒ no forwarding`

and:

`revoked(commit) ⇒ no forwarding`

## 6. Distinguishing T34-C and T34-D

T34-C tests whether a stale PREPARE can be finalized into a commit.

Expected result:

`stale PREPARE → no COMMIT → no forwarding`

T34-D tests a stronger temporal condition:

`valid COMMIT → authority changes → consume`

Expected Strict result:

`stale/revoked COMMIT → no forwarding`

This distinction matters because a system can correctly re-check authority before issuing a commit while still allowing an already-issued commit to survive revocation.

## 7. Scope

T34 demonstrates authority-state semantics only within the tested execution process and controlled forwarding seam.

It does not establish:

- native upstream cMCP support;
- distributed revocation propagation guarantees;
- hardware enforcement;
- resistance to privileged bypasses outside the inspected runtime;
- physical-world safety;
- distributed exactly-once execution.

## 8. Success criterion

T34 is considered experimentally demonstrated only if all strict cases preserve the execution-boundary invariant:

> No effect is produced from a commit whose authority state is no longer valid at the forwarding boundary.

A passing test must show the absence of forwarding, not merely the presence of a denial message.
