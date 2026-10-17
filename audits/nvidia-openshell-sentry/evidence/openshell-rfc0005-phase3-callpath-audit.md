# Focused audit: RFC 0005 Phase 3 vs. CONNECT call path

Date: 2026-10-17  
OpenShell source inspected: `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`  
Audit repository branch: `audit/openshell-sentry-2026-10`  
Scope: source-level conformance check for the generation-consistent authorization cutover. This is not a runtime test report.

## Result

**Disposition: PHASE 3 CUTOVER NOT DEMONSTRATED IN THE INSPECTED CONNECT PATH. NOT A CONFIRMED SECURITY VULNERABILITY.**

The pinned source shows several helper calls after initial authorization, but they are not all independent policy queries. Source inspection of the helper definitions refines the interpretation:

1. `hydrate_tls_mode(&mut decision)` projects TLS mode from the first policy config already present in `decision.endpoint.policy_configs`.
2. `hydrate_l7_route(&mut decision)` builds the L7 route from that same endpoint-config snapshot and tags it with `decision.policy_generation`.
3. `hydrate_destination_plan(&mut decision, ...)` reads `allowed_ips` from that same snapshot and combines it with the exact-declared-host signal and gateway settings.
4. `query_endpoint_credential_guard(...)` is the material independent OPA query among these steps; it calls `engine.query_endpoint_credential_guards(&input)` separately.

The same handler pins `decision.policy_generation` before these calls. It rejects a stale generation, validates the materialized L7 route against the captured generation, races upstream dialing against `wait_until_stale()`, and checks the generation again before returning `200 Connection Established`. These are meaningful safeguards against a straightforward reload race.

Separately, `OpaEngine::authorize_egress()` evaluates `data.openshell.sandbox.egress_authorization` under the engine mutex and returns an `EgressAuthorization` containing the action, endpoint configurations, matched endpoints, exact-declared-host signal and generation. Targeted repository search found call sites in test/supervisor-related code, but did not identify the combined API as the sole source for every Phase 3 field because credential-guard metadata is queried separately. TLS, L7 route and `allowed_ips`/destination planning in the inspected CONNECT path are projections of the initial `EgressDecision` snapshot, not separate OPA evaluations. This is a targeted call-site search, not a formal proof that no other production caller exists.

Therefore, the defensible source finding is limited: **the Phase 3 single-result materialization is not demonstrated by the inspected CONNECT path**. This does not determine whether Phase 3 was planned, in progress, or declared complete for this exact commit. The README describes the single-result cutover as a later step after shadow comparison; the inspected RFC documents do not provide an unambiguous commit-specific phase-status declaration. Until that status is resolved, the separate guard query is a conformance question, not proof of a missed committed requirement. The code inspected also contains generation checks and fail-closed gates, so the source shape alone does not prove mixed-generation use, an authorization bypass, or protected bytes reaching an upstream.

## Requirements from RFC 0005 Phase 3

The implementation plan calls for one OPA result from one policy generation to materialize:

- matched policy/source and matched endpoint;
- destination constraints;
- TLS treatment;
- HTTP enforcement;
- credential plan;
- middleware selection.

It also calls for a generation-pinned request-policy engine, shadow-mode mismatch telemetry, reload-race tests proving each field matches the top-level generation, and stale decisions stopping before upstream request write.

The inspected CONNECT path uses helper steps for TLS, L7 route and destination, but those helpers project fields from the original authorization snapshot. The credential guard is a separate OPA evaluation. The specific Phase 3 gap is therefore not evidence that TLS/L7/destination necessarily mix generations; it is whether the separate credential-guard query and any remaining Phase 3 fields meet the RFC's single-result materialization requirement, and whether runtime behavior remains safe around reloads. Do not infer a runtime vulnerability from this difference.

## Source evidence

- [RFC 0005 implementation plan — Phase 1 and Phase 3](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0005-sandbox-proxy-egress-adapter/implementation-plan.md)
- [RFC 0005 current-shape appendix](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0005-sandbox-proxy-egress-adapter/current-shape.md)
- [CONNECT metadata hydration and generation guard](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2700-L2860)
- [CONNECT stale-generation, credential gate and pre-200 checks](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2860-L3030)
- [Combined authorization implementation](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L600-L675)

## Required next verification

### A. Close the RFC phase-status and source-baseline questions

- Keep the original audit/matrix baseline `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317` separate from this follow-up source review at `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`.
- Determine from a commit-specific RFC/change record whether Phase 3 is planned, in progress, or completed for `b58e24c`. The README describes it as a later cutover after shadow comparison, but the sources inspected here do not declare a definitive status for this commit. Until then, do not classify the transitional shape as a failure to meet a committed milestone.

### B. Complete the source call graph

- Enumerate all production and test call sites of `authorize_egress()`.
- Trace the implementation and result type of each CONNECT hydration helper.
- For each Phase 3 field, record its source, the generation attached to it, and the point at which that generation is checked.
- The current `query_endpoint_credential_guards()` signature returns `Result<Vec<regorus::Value>>`, not a `(result, generation)` pair. In the inspected CONNECT path, alignment is therefore enforced indirectly by the captured `connect_generation_guard` and later `ensure_current()` checks, not by a generation value returned with the guard result. Verify this assumption at both reload windows: reload before/during the guard query and reload after the query but before the final pre-200 check.
- Check whether forward HTTP and other egress paths have equivalent behavior; do not extrapolate CONNECT results to every adapter.

### C. Run tests at the exact source commit

No OpenShell runtime or Cargo tests were executed during this audit step. The audit environment used source inspection through GitHub; it did not run a checkout of OpenShell at the pinned SHA. Accordingly, all runtime and execution claims remain **NOT TESTED**.

In a checkout at `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`, first run the focused existing tests for:
- stale generation rejected before relay context/upstream traffic;
- `credential_guard_does_not_shadow_inspected_endpoint_config`;
- reload/generation guard behavior around CONNECT.

Record the exact commands, toolchain/platform, exit status and relevant output. Do not mark a test PASS merely because a test exists in source.

### D. Add one narrow effect-side race test

Use a harmless canary upstream and synthetic credentials only. Coordinate a policy reload at deterministic barriers before/after the separate credential-guard query and in the upstream-dial window. Capture the authorization generation, guard result/configuration, and whether the canary received a request or protected marker. TLS/L7/destination fields should be checked as projections of the original authorization snapshot, not assumed to be independent OPA reads.

Expected safe behavior:
- no upstream request is written when the decision or any required field is stale/inconsistent;
- no synthetic protected marker reaches the canary under a denied or stale decision;
- every accepted request has a single traceable policy generation and matching endpoint/TLS/credential/destination context.

Avoid timing sleeps as the primary synchronization mechanism. Do not log real credentials.

## Evidence classification

| Claim | Evidence class | Status |
|---|---|---|
| CONNECT calls TLS/L7/destination helper functions; those project from the initial decision snapshot, while credential guard is a separate OPA query | SOURCE | Observed at pinned source |
| Combined `authorize_egress()` evaluates a combined OPA result under the engine mutex | SOURCE | Observed at pinned source |
| The combined API materializes the credential guard and every Phase 3 field in one OPA result | SOURCE | Not demonstrated; credential guard is separately queried |
| A reload can cause mixed-generation authorization to reach upstream | HYPOTHESIS | Not proven |
| A protected request/credential can bypass the intended boundary | RUNTIME | NOT TESTED |
| RFC 0005 Phase 3 is fully complete for all egress adapters | CONFORMANCE | Not demonstrated by this CONNECT inspection alone |

## Decision

Keep OS-06 open as a bounded RFC 0005 conformance and runtime-validation item. Do not label it an exploitable vulnerability unless the field/generation trace and an effect-side test demonstrate an unsafe outcome. The overall OpenShell/Sentry EABC verdict remains **INCONCLUSIVE** until the source baseline is explicitly selected and the relevant execution tests are performed.


## EABC mapping for OS-06 (provisional)

- **INTEGRITY_STATE(B,E):** policy reload and stale-decision transitions must invalidate an in-flight CONNECT before its protected effect is authorized.
- **INTEGRITY_CTX(C,B,E):** credential-guard result must remain aligned with the policy generation and endpoint context used for the primary decision. The guard API currently does not return a generation alongside its values; the handler's captured-generation checks are the claimed binding mechanism and need exact-SHA test evidence.
- **NON_BYPASSABILITY(B,E):** the decisive observation is whether a denied/stale CONNECT can cause any protected request or synthetic credential to reach the upstream canary. The source-level shape alone cannot establish bypassability.
- **INTEGRITY_DEF(B):** the declared boundary is the inspected CONNECT authorization-to-upstream path, not every OpenShell adapter or every Sentry-composed deployment.

This mapping follows the criterion labels used by the audit repository and is provisional until checked against the canonical EABC specification/version used for the wider project.
