# T36 — Authority-State Provenance

## Status

**EXPERIMENTAL TEST PLAN — NOT NATIVE cMCP CONFORMANCE**

T36 adds provenance and authenticity to the authority-state semantics established by T34 and T35.

The question is:

> Can the execution boundary distinguish an authentic, currently valid authority state from a forged, modified, stale, expired, or revoked state that merely contains plausible authority metadata?

T36 intentionally uses an in-process test-double authority and real signature verification. Network transport, key distribution, federation, and HSM semantics remain out of scope.

## 1. AuthorityState

The test authority state contains:

- `authority_ref`
- `authority_epoch`
- `state_digest`
- `issuer`
- `issued_at`
- `valid_from`
- `valid_until`
- `signature`
- `key_id`
- `algorithm`

The signed material is canonicalized before signing and verification.

The signature covers the authority identity, epoch, state digest, issuer, validity interval, key identifier, and algorithm identifier.

## 2. Trust model

The execution boundary is configured with an explicit trusted-issuer/key set.

A state is authentic only when:

1. the issuer/key is trusted;
2. the signature verifies over the canonical state;
3. the authority reference is allowed;
4. the validity interval is satisfied;
5. the state is not explicitly revoked;
6. the epoch satisfies the T35 freshness/current-state rule.

An unrecognized issuer is not implicitly trusted.

## 3. State digest

`state_digest` represents the canonical relevant authority state.

Changing the digest without re-signing MUST invalidate the state.

The digest is not itself a trust credential; it is part of the authenticated state.

## 4. Replay semantics

A correctly signed old state is still authentic cryptographically, but MUST NOT be treated as current authority when its epoch is stale.

Therefore:

`authentic ≠ current`

T36-H explicitly tests this distinction.

## 5. Test matrix

| Case | Scenario | Expected forwarding | Expected effect |
|---|---|---:|---:|
| T36-A | valid provenance + fresh epoch | 1 | 1 |
| T36-B | forged/unknown issuer | 0 | 0 |
| T36-C | modified epoch, signature invalid | 0 | 0 |
| T36-D | modified state digest, signature invalid | 0 | 0 |
| T36-E | correctly signed but stale epoch | 0 | 0 |
| T36-F | unknown authority_ref | 0 | 0 |
| T36-G | valid new epoch + new signature | 1 | 1 |
| T36-H | replayed old signed state | 0 | 0 |
| T36-I | expired validity window | 0 | 0 |
| T36-J | revoked key/issuer | 0 | 0 |

## 6. Required property

For the tested strict profile:

`forwarded ⇒ authentic_provenance(state) ∧ current_authority_state(state) ∧ valid_time(state) ∧ trusted_authority(state)`

Any provenance, trust, freshness, or validity failure MUST result in no forwarding.

The test MUST observe the forwarding seam, not only a denial response.

## 7. Cryptographic scope

T36 proves use of real signature verification over the canonical authority-state representation.

It does not prove:

- secure key generation or storage;
- production key distribution;
- certificate-chain validation;
- HSM behavior;
- remote attestation;
- network transport security;
- federation or multi-authority trust;
- large-scale revocation distribution.

## 8. Relationship to T34/T35

- **T34 — Temporal validity:** authority state must remain valid at consume.
- **T35 — Freshness/distribution:** the boundary must not rely on stale or unavailable state.
- **T36 — Provenance/authenticity:** the boundary must establish why the state is trusted.

Together they establish the tested chain:

`authentic + current + temporally valid authority state → eligible execution boundary`

not merely:

`epoch number looks plausible → forward`.

