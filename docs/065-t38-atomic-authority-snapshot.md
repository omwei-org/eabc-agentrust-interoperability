# T38 — Atomic Authority Snapshot / Commit Linearization

## Status

**EXPERIMENTAL TEST — NOT NATIVE cMCP CONFORMANCE**

T38 formalizes the execution-authority linearization point.

The strict execution-boundary model is:

`PREPARE ≠ AUTHORITY GRANT`

`ATOMIC COMMIT = AUTHORITY GRANT`

At the atomic COMMIT point, the boundary evaluates the exact action against one authoritative snapshot, binds the resulting authority epoch and state digest, and reserves a single-use execution commit.

## Linearization point

`execution_authority_granted_at(commit)` is the unique logical point at which atomic COMMIT succeeds.

All authority predicates used for the grant are evaluated against the same snapshot:

- exact action binding;
- authority provenance;
- current epoch;
- state digest;
- temporal validity;
- current issuer/key trust;
- single-use availability.

A PREPARE result is an optimization hint only. It MUST NOT itself authorize forwarding.

## Strict consume semantics

For Strict mode, COMMIT remains subject to consume-time validity. If the authority state is revoked or its epoch changes before forwarding, consume MUST deny.

Thus a successful COMMIT is an execution-authority grant, but not permission to ignore a subsequent authority transition.

## Test matrix

| Case | Scenario | Expected result |
|---|---|---|
| T38-A | Atomic COMMIT, stable authority | 1 forward, 1 effect |
| T38-B | Authority change before atomic COMMIT | COMMIT denied, 0 effects |
| T38-C | Authority change after COMMIT before consume | consume denied, 0 effects |
| T38-D | Concurrent dual COMMIT for same action | at most 1 successful COMMIT |
| T38-E | PREPARE succeeds, authority changes, COMMIT attempted | COMMIT denied |
| T38-F | Two boundaries, one rotation | only state-valid commit may forward |
| T38-G | Replay after successful consume | denied |
| T38-H | Epoch/state digest bound in COMMIT, then epoch bump | consume denied |

## Required observations

Tests instrument both:

- forwarding entry count;
- effect count.

Where applicable they also count successful atomic commits and successful consumes.

The core property is:

`FORWARD ⇒ atomic_commit_succeeded(snapshot S) ∧ S satisfied all authority predicates at linearization ∧ commit is single-use ∧ strict consume validity holds`

## Scope

T38 demonstrates the semantic linearization point with an in-process controllable authority and real Ed25519 verification.

It does not demonstrate:

- distributed consensus;
- multi-region linearizability;
- persistent transactional logs;
- crash recovery;
- cross-process atomicity;
- production HSM semantics.

Those are separate implementation properties.

## Relationship to T34–T37

T34 establishes temporal validity.

T35 establishes freshness/current-state semantics.

T36 establishes authority-state provenance/authenticity.

T37 establishes current issuer/key trust.

T38 composes these predicates into one atomic execution-authority grant.

The intended state machine is:

`AUTHORIZED ACTION CONTEXT → ATOMIC COMMIT (linearization point) → CONSUME → FORWARD → EFFECT`

with PREPARE explicitly outside the authority-grant transition.
