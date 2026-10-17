# OS-06 — RFC 0005 implementation conformance review

Compared NVIDIA/OpenShell RFC 0005 (`b58e24c9dabd6d4bcf2b7186592d3ad50646541b`) with the pinned CONNECT implementation.
Status: **SOURCE REVIEW — NOT A CONFIRMED SECURITY VULNERABILITY; NO RUNTIME TEST EXECUTED**.

## Finding

RFC 0005 explicitly distinguishes the transitional EgressDecision envelope from the target generation-consistent authorization cutover. The README says the first milestone preserves separate queries and that generation-consistent materialization is a later cutover. The implementation plan's Phase 3 requires one OPA result for matched policy/source, matched endpoint, destination constraints, TLS, HTTP enforcement, credential plan, and middleware selection, plus reload-race tests before upstream request write.

At the pinned source commit, CONNECT still visibly invokes separate hydration/query helpers for TLS mode, credential guard, L7 route, and destination plan after the initial decision. In parallel, `OpaEngine::authorize_egress()` exists and returns a combined authorization result under the engine mutex, but the inspected CONNECT path does not appear to use that method as the sole source for all connection-level metadata. The overlap regression `credential_guard_does_not_shadow_inspected_endpoint_config` verifies that the separate credential guard sees both overlapping endpoint definitions while L7 config and allowed IPs continue to come from the intended inspected endpoint.

Sources:
- [RFC 0005 README: transitional decision and later cutover](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0005-sandbox-proxy-egress-adapter/README.md)
- [RFC 0005 Phase 3 acceptance requirements](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0005-sandbox-proxy-egress-adapter/implementation-plan.md)
- [CONNECT metadata hydration sequence](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2700-L2860)
- [Combined authorization snapshot](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L600-L675)
- [Overlapping L4/L7 credential guard regression](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L9612-L9705)

## Assessment

- This is a **conformance / milestone-status question**, not evidence by itself that a request bypasses enforcement. Existing mutex and generation guards materially mitigate the simple reload-race hypothesis.
- The combined query's existence alone does not prove Phase 3 is complete; the call path must show that all required connection-level fields come from that one result and that legacy query paths are no longer authoritative.
- Conversely, separate helpers do not establish a race if each query is serialized and stale generations are rejected before protected traffic can flow.
- The overlapping endpoint test confirms an intentional distinction: credential gating must aggregate across both L4 and inspected definitions, while endpoint TLS/SSRF metadata must not be shadowed by the L4 credential endpoint. A future single-result schema must preserve that distinction rather than blindly collapsing all endpoints to one record.

## Recommended next verification

1. Trace every caller of `authorize_egress()` and establish whether CONNECT and forward HTTP use it in the pinned revision.
2. Compare `EgressAuthorization` fields with the Phase 3 required materialization list; explicitly account for destination constraints, TLS, protocol, credential plan, and middleware selection.
3. Run existing overlap and stale-generation regression tests in a checkout at the exact SHA; record commands and exit codes.
4. If the repository is runnable, add a narrowly scoped test asserting the connection-level metadata's source generation and canary-observed no-write behavior on stale decisions. Do not add timing sleeps or claim a vulnerability from source shape alone.

**Disposition:** keep OS-06 open as a bounded RFC-conformance / runtime-validation item. Do not label it exploitable. GEN-01 through GEN-04 remain **NOT TESTED**.

## Follow-up: call-site and current-shape check

A second targeted search for `authorize_egress` surfaced the API definition and test-oriented call sites, but did not surface a production CONNECT call site. The inspected CONNECT handler still performs this sequence on its `decision` object:

1. `hydrate_tls_mode(&mut decision)`
2. `query_endpoint_credential_guard(...)`
3. `hydrate_l7_route(&mut decision)`
4. `hydrate_destination_plan(&mut decision, ...)`

The RFC's own `current-shape.md` describes endpoint metadata lookup and policy evaluation as interleaved, and its implementation plan explicitly labels Phase 1's `EgressDecision` as transitional compatibility hydration—not an atomic OPA result. Phase 3 then calls for one result to materialize the connection-level fields and for shadow-mode mismatch telemetry before cutover.

This strengthens the **conformance-status** concern: the combined API's presence must not be mistaken for evidence that the CONNECT path has completed the Phase 3 cutover. Search results are not a formal whole-repository call-graph proof, so the safe wording is that no production CONNECT call site was found in this targeted inspection, not that none can exist anywhere.

Sources:
- [Current-shape appendix](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0005-sandbox-proxy-egress-adapter/current-shape.md)
- [Phase 1 transitional decision contract and Phase 3 cutover](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0005-sandbox-proxy-egress-adapter/implementation-plan.md)
- [Observed CONNECT hydration sequence](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2700-L2860)
- [Combined authorization API](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L600-L675)

### Revised disposition

Keep OS-06 as **RFC Phase 3 cutover not yet demonstrated in the inspected CONNECT call path**, pending complete call-graph verification and exact-SHA tests. This is an implementation-conformance gap / unverified milestone, not a demonstrated policy bypass. Existing generation guards and per-query locking remain meaningful mitigations. No runtime test was executed; GEN-01 through GEN-04 remain **NOT TESTED**.
