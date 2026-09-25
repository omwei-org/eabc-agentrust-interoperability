# T35 — Distributed / External Authority State

## Status

**EXPERIMENTAL TEST PLAN — NOT NATIVE cMCP CONFORMANCE**

T35 extends T34 from an in-process authority variable to an external authority-state provider.

The question is no longer only whether a forwarding boundary checks an epoch. It is:

> How does the execution boundary obtain sufficiently fresh authority state when authority and execution enforcement are separate components?

## 1. Core property

A strict distributed execution boundary MUST NOT treat a stale or unavailable authority snapshot as current authority.

The required property is:

`forwarded ⇒ trusted_current_authority_state(commit)`

For epoch-based authority:

`forwarded ⇒ commit.authority_epoch = authoritative_current_epoch`

If the execution boundary cannot establish that equality with the required freshness semantics, it MUST deny forwarding.

## 2. Authority topology

The model is:

`Authority Source`
→ `authority state / epoch`
→ `trusted propagation or read`
→ `EABC execution boundary`
→ `consume(commit)`
→ `existing forwarding seam`

The authority source MAY be:

- an EABC authority service;
- a local privileged authority component;
- a hardware-backed SLC;
- another trusted state provider.

T35 does not prescribe transport, consensus, replication, or storage.

## 3. Freshness contract

The execution boundary needs an explicit freshness rule.

A native implementation SHOULD expose enough information to establish:

- authority epoch/version;
- authority validity/revocation state;
- state provenance;
- freshness/version monotonicity;
- availability of the authoritative state.

A cached snapshot without a freshness guarantee MUST NOT be silently treated as current authority.

If required authority state cannot be obtained or validated, Strict mode MUST fail closed.

## 4. Test matrix

| Case | Scenario | Expected forwarding | Expected effect |
|---|---|---:|---:|
| T35-A | external authority stable and fresh | 1 | 1 |
| T35-B | external revocation observed before consume | 0 | 0 |
| T35-C | revocation exists but execution boundary has stale cached epoch | 0 | 0 |
| T35-D | authority source unavailable / freshness cannot be established | 0 | 0 |
| T35-E | authority update propagates, then valid new epoch commit | 1 | 1 |
| T35-F | two execution boundaries observe same authoritative revocation | 0 | 0 |

## 5. Stale-cache rule

T35-C is intentionally stronger than T34.

If:

`commit.epoch = cached_epoch`

but:

`cached_epoch < authoritative_epoch`

the execution boundary MUST NOT forward merely because its local cache still agrees with the commit.

This is the distributed form of the T34 temporal property.

## 6. Fail-closed rule

For Strict execution-boundary semantics:

`authority_state unavailable ∨ authority_state freshness unknown ⇒ no forwarding`

This prevents loss of connectivity to the authority source from silently becoming permission to execute.

## 7. What T35 demonstrates

A passing T35 experiment demonstrates only that the tested execution boundary:

- obtains authority state from an externalized provider;
- rejects stale state;
- rejects unavailable/unknown state;
- accepts a commit after authoritative state has advanced and the commit is bound to that new state;
- applies the same rule at multiple execution boundaries.

It does not demonstrate distributed consensus, Byzantine fault tolerance, network partition safety in general, or hardware enforcement.

## 8. Native integration implication

T35 adds one requirement to the T33/T33.1 contract:

> Authority state used by the execution boundary must have an explicit freshness/provenance semantic. An execution boundary MUST NOT infer current authority from an unqualified local cache.

The implementation mechanism remains outside the normative contract.
