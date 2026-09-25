# T32–T38 — EABC Execution Authority State Machine and Composed Invariant

## Status

**SYNTHESIS / EXPERIMENTAL EVIDENCE MODEL — NOT NATIVE cMCP CONFORMANCE**

This document composes T32–T38 into one execution-authority state machine and one fail-closed invariant. It adds no runtime test.

## 1. State machine

States:

- **AUTHORIZED** — cMCP/AgenTrust authorization accepted the action.
- **COMMIT_PENDING** — optional PREPARE/non-granting phase.
- **COMMITTED** — atomic COMMIT succeeded; execution authority was granted.
- **CONSUMED** — commit was successfully consumed at the forwarding boundary.
- **DENIED** — terminal failure before execution.
- **EXPIRED / REVOKED** — terminal invalidation under Strict semantics.

Transitions:

`AUTHORIZED → COMMIT_PENDING`: optional PREPARE; no authority grant.

`AUTHORIZED → COMMITTED`: atomic COMMIT succeeds against a valid authority snapshot.

`AUTHORIZED → DENIED`: authority predicates fail.

`COMMIT_PENDING → COMMITTED`: atomic COMMIT succeeds after authoritative re-evaluation.

`COMMIT_PENDING → DENIED`: prepared context is stale, revoked, unauthenticated, untrusted, or otherwise invalid.

`COMMITTED → CONSUMED`: consume succeeds and forwarding is entered.

`COMMITTED → DENIED / REVOKED / EXPIRED`: Strict consume validity fails.

`CONSUMED → DENIED`: subsequent consume; no second successful execution.

Core rules:

1. PREPARE is non-granting.
2. Atomic COMMIT is the execution-authority linearization point.
3. COMMIT binds the exact action to the authority snapshot.
4. CONSUME is single-use.
5. Every production-reachable forwarding path for a correlated execution must satisfy execution admission.
6. MANDATORY requires EABC admission for every tool call.
7. OPTIONAL permits a non-correlated legacy path; this is **LEGACY_NON_CORRELATED**, not an EABC bypass.

## 2. Composed invariant

For a correlated execution:

`FORWARD(commit) ⇒
atomic_commit_succeeded(commit, S)
∧ exact_action_binding(commit, action_tuple)
∧ single_use(commit)
∧ authentic_provenance(S)
∧ current_freshness(S)
∧ temporally_valid(S)
∧ issuer_currently_trusted(S)
∧ commit.authority_epoch = S.epoch
∧ commit.state_digest = S.state_digest
∧ consume_valid_under_strict(commit)`

Fail-closed:

`¬(all required predicates) ⇒ ¬FORWARD ⇒ ¬EFFECT`

This is a property of the tested execution boundary, not a claim about independent upstream behavior.

## 3. Evidence map

| Component | Primary evidence |
|---|---|
| Forwarding seam / exclusivity | T32 |
| Integration contract | T33 |
| Temporal validity | T34 |
| Freshness / no stale state | T35 |
| Provenance / authenticity | T36 |
| Trust lifecycle / key rotation | T37 |
| Atomic linearization point | T38 |
| Exact action binding | T32 / T33 |
| Single-use | T32 / T33 / T38-D / T38-G |
| Fail-closed boundary | T32–T38 |

These are experimental evidence links; they do not imply native cMCP conformance.

## 4. Role separation

`INTENT → AUTHORIZATION → EXECUTION AUTHORITY → COMMIT → EFFECT`

cMCP/AgenTrust may establish identity, attestation, policy authorization, audit and TRACE context.

EABC establishes the execution-authority conditions under which the authorized action may cross the execution boundary.

## 5. Strict semantics

A previously issued commit does not create immunity from subsequent authority invalidation. If before consume the epoch changes, state becomes stale, issuer/key is revoked, provenance fails, validity expires, or the bound digest no longer represents the authoritative state, consume MUST fail closed and forwarding MUST NOT occur.

## 6. Evidence boundary / non-claims

> In the controlled execution-boundary model tested against the pinned cMCP runtime surface, execution authority can be represented as a single-use, exact-action-bound commit granted at an atomic logical linearization point and consumed only while its authority state remains authentic, current, temporally valid and trusted.

This does **not** establish distributed or multi-node atomicity, global linearizability without consensus, production key-distribution semantics, HSM-backed enforcement, multi-region convergence, privileged-bypass resistance, physical/hardware isolation, exactly-once external physical-world effect, or native cMCP conformance.

## 7. T39 boundary

**T39 — Adversarial Composition / Invariant Violation** should compose existing predicates rather than introduce another independent semantic property.

Candidate compositions: stale state + replay; valid old signature + revoked key; PREPARE + epoch rotation + COMMIT; valid COMMIT + consume-time revocation; action substitution + authority-state substitution; concurrent COMMIT + key rotation; replay + concurrent consume.

T39 should retain forwarding entry count, effect count, successful COMMIT count, and successful consume count as decisive observables.
