# T37 — Authority Key Lifecycle / Trust Transition

## Status

**EXPERIMENTAL TEST PLAN — NOT NATIVE cMCP CONFORMANCE**

T37 extends T36 from provenance verification to the lifecycle of the trust anchor used to authenticate authority state.

The question is:

> Can the execution boundary distinguish a state signed by a key that was once trusted from a state signed by a key that is currently trusted?

This is a trust-transition property, not a new execution-token format.

## 1. Trust model

The execution boundary maintains an explicit trust configuration:

`issuer -> key_id -> trusted / revoked`

A signature is insufficient by itself. The signing key must be trusted under the authority state applicable at consume.

Trust transitions are modeled as:

`KEY_A trusted → KEY_A revoked / retired → KEY_B trusted`

The transition is explicit. T37 does not prescribe how production trust configuration is distributed.

## 2. Required semantics

At consume, the execution boundary MUST establish:

1. the authority state signature is valid;
2. the signing key is currently trusted;
3. the authority reference is allowed;
4. the state is temporally valid;
5. the state is current under T35;
6. the commit is bound to that state.

A correctly signed state from a retired/revoked key MUST be denied.

A correctly signed state from a newly trusted key MAY be accepted only after the trust transition is active.

## 3. Test matrix

| Case | Scenario | Expected forwarding | Expected effect |
|---|---|---:|---:|
| T37-A | KEY_A trusted, valid state | 1 | 1 |
| T37-B | KEY_A revoked, old state replayed | 0 | 0 |
| T37-C | KEY_B not yet trusted | 0 | 0 |
| T37-D | KEY_B activated, fresh state | 1 | 1 |
| T37-E | old KEY_A state after KEY_B activation | 0 | 0 |
| T37-F | forged signature under unknown key | 0 | 0 |
| T37-G | key rotation between state verification and consume | 0 | 0 |
| T37-H | two execution boundaries apply same trust transition | consistent: 0 for old key, 1 for new trusted key | consistent |

## 4. Transition atomicity

The critical race is T37-G.

If trust changes after an authority state has been verified but before execution consume, the execution boundary MUST re-evaluate the current trust configuration or otherwise use an atomic trust snapshot.

For Strict semantics:

`verified_under_old_trust ∧ current_trust_revokes_key ⇒ no forward`

A previously verified signature MUST NOT create a durable authorization to execute.

## 5. Fail-closed rule

`unknown_key ∨ revoked_key ∨ trust_state_unavailable ⇒ no forwarding`

The last condition is intentionally conservative for Strict mode: if current trust cannot be established, the execution boundary cannot establish that the issuer remains trusted.

## 6. Scope

T37 demonstrates trust lifecycle semantics using an in-process controllable trust store and real Ed25519 verification.

It does not demonstrate:

- secure distribution of trust configuration;
- certificate-chain semantics;
- HSM-backed key lifecycle;
- multi-party trust governance;
- distributed consensus;
- cross-region convergence;
- production key compromise recovery.

Those are subsequent integration concerns.

## 7. Relationship to T34–T36

- **T34 — Temporal validity:** authority remains valid at consume.
- **T35 — Freshness/distribution:** authority state is current rather than stale.
- **T36 — Provenance/authenticity:** state was genuinely signed by an issuer/key.
- **T37 — Trust lifecycle:** that issuer/key remains trusted at consume.

Together:

`forwarded ⇒ authentic ∧ current ∧ temporally_valid ∧ currently_trusted authority state`

