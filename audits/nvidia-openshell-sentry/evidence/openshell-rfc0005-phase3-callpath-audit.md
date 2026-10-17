# Focused audit: RFC 0005 Phase 3 vs. CONNECT call path

Date: 2026-10-17  
OpenShell source inspected: `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`  
Audit repository branch: `audit/openshell-sentry-2026-10`  
Scope: source-level conformance check for the generation-consistent authorization cutover. This is not a runtime test report.

## Result

**Disposition: PHASE 3 CUTOVER NOT DEMONSTRATED IN THE INSPECTED CONNECT PATH. NOT A CONFIRMED SECURITY VULNERABILITY.**

The pinned source shows that the CONNECT handler still materializes security-relevant metadata through multiple helper calls after its initial policy decision:

1. `hydrate_tls_mode(&mut decision)`
2. `query_endpoint_credential_guard(...)`
3. `hydrate_l7_route(&mut decision)`
4. `hydrate_destination_plan(&mut decision, ...)`

The same handler pins `decision.policy_generation` before these calls. It rejects a stale generation, validates the materialized L7 route against the captured generation, races upstream dialing against `wait_until_stale()`, and checks the generation again before returning `200 Connection Established`. These are meaningful safeguards against a straightforward reload race.

Separately, `OpaEngine::authorize_egress()` evaluates `data.openshell.sandbox.egress_authorization` under the engine mutex and returns an `EgressAuthorization` containing the action, endpoint configurations, matched endpoints, exact-declared-host signal and generation. Targeted repository search found test-oriented/supervisor call sites, but did not identify this combined API as the sole source of the CONNECT handler's TLS, credential-guard, L7-route and destination-plan metadata. This is a targeted-search result, not a formal proof that no other production caller exists.

Therefore, the defensible finding is about **milestone/conformance status**: Phase 3's single-result materialization is not demonstrated by the inspected CONNECT path. The code inspected also contains generation checks and fail-closed gates, so the source shape alone does not prove mixed-generation use, an authorization bypass, or protected bytes reaching an upstream.

## Requirements from RFC 0005 Phase 3

The implementation plan calls for one OPA result from one policy generation to materialize:

- matched policy/source and matched endpoint;
- destination constraints;
- TLS treatment;
- HTTP enforcement;
- credential plan;
- middleware selection.

It also calls for a generation-pinned request-policy engine, shadow-mode mismatch telemetry, reload-race tests proving each field matches the top-level generation, and stale decisions stopping before upstream request write.

The inspected CONNECT path visibly performs separate hydration/query steps for TLS, credential guard, L7 route and destination. Whether every item in the Phase 3 list is implemented elsewhere or whether the transition is intentionally still in progress requires a complete call graph and field-by-field trace. Do not infer a runtime vulnerability from this difference.

## Source evidence

- [RFC 0005 implementation plan — Phase 1 and Phase 3](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0005-sandbox-proxy-egress-adapter/implementation-plan.md)
- [RFC 0005 current-shape appendix](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0005-sandbox-proxy-egress-adapter/current-shape.md)
- [CONNECT metadata hydration and generation guard](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2700-L2860)
- [CONNECT stale-generation, credential gate and pre-200 checks](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2860-L3030)
- [Combined authorization implementation](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L600-L675)

## Required next verification

### A. Complete the source call graph

- Enumerate all production and test call sites of `authorize_egress()`.
- Trace the implementation and result type of each CONNECT hydration helper.
- For each Phase 3 field, record its source, the generation attached to it, and the point at which that generation is checked.
- Check whether forward HTTP and other egress paths have equivalent behavior; do not extrapolate CONNECT results to every adapter.
- Determine whether the RFC labels Phase 3 as planned, in progress, or completed for this exact commit.

### B. Run tests at the exact source commit

No OpenShell runtime or Cargo tests were executed during this audit step. The audit environment used source inspection through GitHub; it did not run a checkout of OpenShell at the pinned SHA. Accordingly, all runtime and execution claims remain **NOT TESTED**.

In a checkout at `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`, first run the focused existing tests for:
- stale generation rejected before relay context/upstream traffic;
- `credential_guard_does_not_shadow_inspected_endpoint_config`;
- reload/generation guard behavior around CONNECT.

Record the exact commands, toolchain/platform, exit status and relevant output. Do not mark a test PASS merely because a test exists in source.

### C. Add one narrow effect-side race test

Use a harmless canary upstream and synthetic credentials only. Coordinate a policy reload at deterministic barriers between authorization and metadata materialization, and in the upstream-dial window. The test should capture the generation associated with every materialized field and whether the canary received a request or protected marker.

Expected safe behavior:
- no upstream request is written when the decision or any required field is stale/inconsistent;
- no synthetic protected marker reaches the canary under a denied or stale decision;
- every accepted request has a single traceable policy generation and matching endpoint/TLS/credential/destination context.

Avoid timing sleeps as the primary synchronization mechanism. Do not log real credentials.

## Evidence classification

| Claim | Evidence class | Status |
|---|---|---|
| CONNECT calls separate TLS, credential-guard, L7-route and destination hydration helpers | SOURCE | Observed at pinned source |
| Combined `authorize_egress()` evaluates a combined OPA result under the engine mutex | SOURCE | Observed at pinned source |
| The combined API is the sole source for all CONNECT metadata | SOURCE | Not demonstrated in targeted call-path inspection |
| A reload can cause mixed-generation authorization to reach upstream | HYPOTHESIS | Not proven |
| A protected request/credential can bypass the intended boundary | RUNTIME | NOT TESTED |
| RFC 0005 Phase 3 is fully complete for all egress adapters | CONFORMANCE | Not demonstrated by this CONNECT inspection alone |

## Decision

Keep OS-06 open as a bounded RFC 0005 conformance and runtime-validation item. Do not label it an exploitable vulnerability unless the field/generation trace and an effect-side test demonstrate an unsafe outcome. The overall OpenShell/Sentry EABC verdict remains **INCONCLUSIVE** until the source baseline is explicitly selected and the relevant execution tests are performed.
