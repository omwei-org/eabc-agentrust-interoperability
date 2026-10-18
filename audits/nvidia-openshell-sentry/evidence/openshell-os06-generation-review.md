# OS-06 follow-up — authorization generation and credential guard

Review date: 2026-10-17  
Original audit baseline: `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`  
Follow-up source commit: `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`  
Runtime status: **NOT TESTED**. This is a source/RFC comparison and test-plan refinement, not a runtime test report. The two SHAs are separate evidence baselines; this follow-up does not silently rebase the original findings or test matrix.

## Question

Does the implementation ensure that the L4 authorization decision, endpoint metadata used for TLS/L7 and credential handling, and relay enforcement all refer to one policy generation? Does it fail closed when a policy reload occurs during connection setup or while a relay is active?

## RFC comparison

The RFC's `current-shape.md` at the pinned baseline explicitly states that L4 authorization, L7 route, TLS mode, `allowed_ips`, and exact-declared-host metadata were materialized through separate engine calls and that sibling metadata queries were not all asserted against the L4 decision generation. It identifies mixed-generation materialization as a risk and states the target: all policy-derived fields must come from one generation and stale decisions must be rejected before an upstream request is written.

The RFC implementation plan's Phase 3 calls for one OPA result containing matched policy/source, endpoint, destination constraints, TLS, HTTP enforcement, credential plan and middleware selection; shadow-mode comparison; and reload-race tests. This is an explicit target/plan, not evidence that the full cutover was completed.

References:
- [RFC current-shape at baseline](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/rfc/0005-sandbox-proxy-egress-adapter/current-shape.md#L221-L240)
- [RFC implementation plan at baseline](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/rfc/0005-sandbox-proxy-egress-adapter/implementation-plan.md#L66-L82)

## Follow-up source evidence at `b58e24c`

### Controls observed

- CONNECT checks the captured connection generation against the L7 route generation before proceeding with upstream connection setup. A mismatch is rejected through the stale-policy path.
  - [CONNECT credential guard and route-generation check](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2899-L2944)
- Relay setup validates that the route's `l7_policy_generation` equals the expected L4 decision generation.
  - [`validate_route_generation`](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy/relay.rs#L110-L132)
- A `PolicyGenerationGuard` compares the captured generation with the current generation and can wait for a generation change, supporting closure of stale relays.
  - [Generation guard](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L195-L240)
- Credential guard aggregation considers all matching credentialed endpoint guards and is conservative across them: uninspected credentials are allowed only if all relevant credentialed matches opt in; L7 protocol presence likewise must hold across the matches. CONNECT rejects credentialed raw-tunnel use unless explicitly permitted.
  - [Credential guard aggregation](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L4008-L4054)
  - [OPA overlapping-endpoint regression test](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L9612-L9690)

### What this does and does not settle

These are meaningful source-level controls. They narrow the hypothesis: it would be inaccurate to say that the implementation has no generation guard or that credentialed L4 fallback is always permitted.

They do not, by themselves, establish that every sibling metadata field (credential guard, TLS mode, destination allowlist and exact-host signals) is materialized atomically from the same generation as the primary L4 decision. In the inspected source, the explicit equality check is visible for the L7 route generation; the separate credential-guard query is passed the already-created decision's identity fields but does not visibly take an expected-generation argument at its call boundary. This is a race-test lead, not proof of a defect: the engine may serialize or otherwise constrain the relevant state, and runtime ordering must be established before making a vulnerability claim.

The source-level discrepancy is **partially narrowed, not fully closed**. Source shows route-generation rejection and stale-relay machinery, and TLS/L7/destination values in the inspected CONNECT path are projections of the original snapshot. The credential guard is a separate OPA evaluation; its API returns values without a paired generation, while CONNECT relies on its captured generation guard and later checks. The broad mixed-generation claim for TLS/L7/destination is not supported by this source trace. The remaining conformance question depends on whether Phase 3 was declared planned, in progress or complete for the exact commit; the RFC sources inspected describe it as a later cutover after shadow comparison but do not establish a commit-specific completion status.

## GEN-01 through GEN-04 — runtime falsification plan

Run only in an isolated lab with synthetic credentials, harmless canary payloads, deterministic barriers and a canary upstream that independently records accepted paths, request bodies and whether a synthetic credential was present. Do not log raw secrets.

1. **GEN-01 — authorization versus credential guard:** pause after the main L4 decision and before/after credential-guard evaluation. Reload in both directions: raw/L4 allowed to inspected credential-constrained, and inspected to raw/L4. Record every captured/current generation and whether CONNECT is accepted.
2. **GEN-02 — final check versus CONNECT success:** pause after the final generation validation and before success is returned/relay setup completes. Publish a new policy generation. Determine whether any protected bytes or injected credential reach the canary.
3. **GEN-03 — active relay invalidation:** establish raw, REST/L7 and long-lived relays, then publish a new generation or fail-closed quarantine. Confirm stale relays close and no protected bytes/credentials are accepted after the applicable invalidation point.
4. **GEN-04 — metadata materialization sequence:** add barriers around L4 authorization, L7 route, credential guard, TLS mode, destination allowlist/exact-host metadata and relay startup. Reload at each boundary and repeat with overlapping L4/L7 endpoints, malformed/missing metadata and explicit opt-in.

For each run, capture commit, driver/platform, effective policy hash, old/new generation, barrier schedule, OPA/proxy traces, client transcript, upstream canary records and relay-close timing. A supervisor denial log alone is insufficient to establish that the upstream received no protected data.

**Expected safe result:** no mixed-generation decision may authorize a protected upstream request; stale CONNECT is rejected/closed before protected bytes or credentials arrive; active stale relays close; explicit `allow_uninspected_credentials: true` affects only the endpoint and scope represented by the effective policy.

**Status:** all four rows remain **NOT TESTED**. No runtime attempt was performed as part of this follow-up.


## Addendum — deeper engine-lock and authorization-snapshot inspection

Follow-up source inspection at the same pinned OpenShell commit materially narrows the remaining hypothesis:

- `OpaEngine::authorize_egress()` holds the engine mutex while it captures `current_generation()` and evaluates `data.openshell.sandbox.egress_authorization`. The returned `EgressAuthorization` includes action, endpoint configs, matched endpoints, exact-declared-host signal, and the generation captured under that lock.
- TLS mode and L7 route are hydrated from the already materialized `EgressDecision` endpoint snapshot; they are not separate policy-engine reads in this CONNECT path.
- The credential-guard query is separate, but it also obtains the same engine mutex for its OPA evaluation. Reload paths take that mutex before replacing the engine and advancing generation. Therefore the query itself is serialized against reload; its result is not an unsynchronized read of a mutating engine.
- CONNECT later races upstream dialing against `connect_generation_guard.wait_until_stale()` and checks `ensure_current()` after dialing, before writing CONNECT success. Relay paths also carry generation guards.

Source references:
- [Single-result authorization under engine mutex](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L600-L675)
- [Reload lock and generation publication](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L735-L830)
- [CONNECT generation guard, credential guard, route validation and dial guard](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2700-L2965)

**Revised interpretation:** the broad claim that CONNECT's TLS, L7 route, destination metadata, and top-level authorization are independently queried and can therefore mix generations is not supported by this inspected path. Most of those fields come from one authorization snapshot. The remaining runtime question is narrower: whether a reload around the separate credential-guard query, upstream dial completion, CONNECT success, or relay startup can produce an externally observable policy violation despite the generation guard. The source indicates that the credential-guard OPA evaluation is serialized against reload by the engine mutex, but the guard result itself is not returned with a generation. The exact safety claim to test is therefore the handler's generation binding and protected-effect outcome, not an assumed concurrent mutation of the OPA engine. Source inspection is not a runtime falsification test.

GEN-01 should now focus on proving the serialisation/guard behavior rather than assuming mixed-generation metadata. GEN-02 should test the final-check-to-CONNECT-success boundary and independently observe whether a stale relay can carry any protected bytes. GEN-03 should reuse existing relay-reload regression tests and add upstream-side observation only where missing. GEN-04 should not repeat the disproven premise that TLS and L7 are separate OPA queries in this CONNECT path; target only fields actually queried independently and paths not covered by the snapshot.

**Status remains:** GEN-01 through GEN-04 **NOT TESTED**.
