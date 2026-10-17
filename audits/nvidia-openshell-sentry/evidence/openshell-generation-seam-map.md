# GEN test seam map — pinned source review

Reviewed source: NVIDIA/OpenShell commit `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`.
Status: **SOURCE REVIEW ONLY — NO RUNTIME TESTS EXECUTED**.

## Confirmed code order for CONNECT

1. L4 decision is produced in `proxy.rs` in the CONNECT handler.
2. `relay::pin_policy_generation(&opa_engine, decision.policy_generation)` captures a generation guard; failure rejects stale CONNECT.
3. `hydrate_tls_mode(&mut decision)` derives TLS mode from the decision snapshot.
4. `query_endpoint_credential_guard(&opa_engine, &decision, &host_lc, port)` separately queries credential guard using the decision's identity fields.
5. `hydrate_l7_route(&mut decision)` materializes the L7 route snapshot.
6. `hydrate_destination_plan(...)` and destination validation run before upstream dialing.
7. The code checks `credential_guard.blocks_connect()` and then validates the L7 route generation against the captured generation before `dial_upstream` and before returning CONNECT 200.

Relevant source:
- [CONNECT authorization and generation pinning](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2700-L2855)
- [Credential guard and route generation checks](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2850-L2960)
- [Credential guard query implementation](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L3990-L4055)
- [Generation guard implementation](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L195-L240)
- [Route-generation validator](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy/relay.rs#L105-L135)

## Test-seam requirements

- **GEN-01:** the best seam is between generation pinning / TLS hydration and the credential guard query, plus one after the query. The current function is synchronous at the call site, but its underlying OPA query path may be sync; use a test-only hook/barrier inside a test harness rather than a sleep. Verify the policy engine reload semantics and generation update order before interpreting the race.
- **GEN-02:** place a hook after `validate_route_generation` and before `dial_upstream` / `200 Connection Established`. The source excerpt shows the validation precedes dialing; confirm the exact `200` write location at the pinned commit before adding a barrier.
- **GEN-03:** use the `PolicyGenerationGuard::wait_until_stale` relay select branch and existing close behavior. Test raw and inspected relays separately; if the raw path does not use this guard, document that fact and trace the raw relay shutdown branch.
- **GEN-04:** hooks are required around the full sequence above, especially the separate credential-guard query. For TLS and destination policy, distinguish fields read from the `EgressDecision` snapshot from independent engine queries; do not assume a race exists merely because helper functions are separate.

## Important limitation

The inspected CONNECT path already pins a generation, derives TLS mode from the decision snapshot, stamps the hydrated L7 route with `decision.policy_generation`, checks route-generation equality before dialing, and uses a generation guard for stale relay handling. This materially lowers the plausibility of a simple mixed-generation CONNECT race. The credential guard is a separate engine query, but its query implementation and engine locking/reload semantics must be inspected together before claiming it can observe a different policy generation.

To proceed from source review to a genuine runtime result, obtain a runnable checkout/build environment for this exact commit, add deterministic test-only barriers, and run the canary-backed scenarios. GitHub source reads alone cannot establish runtime behavior.

**Disposition:** all GEN scenarios remain **NOT TESTED**.