# T39 — Adversarial Composition / Invariant Violation

**EXPERIMENTAL COMPOSITION TEST — NOT NATIVE cMCP CONFORMANCE**

T39 attacks the composed execution-authority invariant established by T32–T38. It introduces no new semantic predicate.

## Objective

Within the tested composition space derived from T32–T38, can a combination of known authority-state violations reach the forwarding boundary or produce the declared effect?

## Modes

### T39-VALID
Positive control: valid action → valid atomic COMMIT → valid consume → FORWARD → EFFECT. Expected: one successful COMMIT, one successful consume, one forwarding entry, one effect.

### T39-ADV
Adversarial composition of two or more existing violation dimensions. An invariant violation occurs if an invalid composition produces any forwarding entry or effect.

## Violation catalogue

V1 missing COMMIT; V2 replayed COMMIT; V3 action substitution; V4 stale/mismatched epoch; V5 state-digest mismatch; V6 forged/invalid signature; V7 unknown/untrusted issuer; V8 key revocation after verification and before consume; V9 expired validity; V10 authority unavailable; V11 concurrent dual consume; V12 PREPARE followed by invalidation and COMMIT attempt; V13 authority change before atomic COMMIT; V14 post-COMMIT revocation/epoch bump under Strict semantics.

## Matrix

| Case | Mode | Composition | Expected |
|---|---|---|---|
| T39-A | VALID | all predicates valid | 1 forward / 1 effect |
| T39-B | ADV | replay + action substitution | 0 / 0 |
| T39-C | ADV | stale epoch + valid signature | 0 / 0 |
| T39-D | ADV | verify + key revocation + consume | 0 / 0 |
| T39-E | ADV | forged issuer + epoch bump | 0 / 0 |
| T39-F | ADV | concurrent dual consume | ≤1 / ≤1 |
| T39-G | ADV | PREPARE + multiple invalidations + COMMIT | 0 / 0 |
| T39-H | ADV | post-COMMIT revocation + digest mismatch | 0 / 0 |
| T39-I | ADV | property-based random composition | 0 / 0 for every invalid case |
| T39-J | VALID | valid path after adversarial sequence | 1 / 1 |

## Property-based composition

T39-I samples combinations of V1–V14 from a deterministic seed. It explores combinations beyond the hand-selected matrix but is not an exhaustive security proof.

For every invalid generated composition: forwarding_entry_count = 0 and effect_count = 0.

## Evidence boundary

A PASS supports: within the tested adversarial compositions of authority-state violations derived from T32–T38, no invalid composition produced a forwarding entry or effect, while the valid control continued to produce exactly one COMMIT → CONSUME → FORWARD → EFFECT path.

## Non-claims

No exhaustive attack-space coverage, distributed atomicity, global linearizability, production key distribution, HSM semantics, privileged-bypass resistance, physical/hardware isolation, exactly-once physical-world effect, or native cMCP conformance.
