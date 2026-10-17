# GEN-01 regression coverage review

Reviewed against NVIDIA/OpenShell source commit `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`.
Status: **SOURCE/TEST DISCOVERY ONLY — NOT EXECUTED HERE**.

## Existing coverage found

1. `crates/openshell-supervisor-network/src/proxy/relay.rs` contains `stale_generation_fails_before_relay_context_is_created()`. This is direct unit-test evidence that stale generations are rejected before an HTTP relay context is created.
2. `crates/openshell-supervisor-network/src/opa.rs` implements `authorize_egress()` by holding the engine mutex while capturing `current_generation()` and evaluating the combined `egress_authorization` rule. The authorization returns its generation and policy-derived endpoint metadata together.
3. `OpaEngine::reload()` acquires the same engine mutex before replacing the compiled engine and advancing the generation. The policy+middleware+credentials reload path also takes the engine mutex and advances generation as part of publication.
4. CONNECT uses a generation guard while dialing upstream, rejects if the guard becomes stale, and validates the L7 route generation before CONNECT success. The relay path retains a generation-pinned policy primitive.
5. Credential-guard aggregation has an OPA regression test for overlapping L4 and inspected endpoint definitions, and `query_endpoint_credential_guards()` is a distinct API called from the CONNECT setup path.

Source pointers:
- [Stale relay-context regression](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy/relay.rs)
- [Authorization snapshot and reload lock](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L600-L830)
- [CONNECT credential guard and generation-gated dial](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2700-L2965)
- [Credential-guard aggregation](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L3990-L4055)
- [Overlapping-endpoint OPA regression](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L9612-L9690)

## What the discovered tests do not establish by themselves

- A unit test that rejects a stale relay context does not prove an independently observed upstream received no protected bytes in every CONNECT timing window.
- The overlap regression tests policy aggregation/precedence, not necessarily a reload interleaving at the credential-guard call boundary.
- Source-level mutex ordering supports serialization, but only a test exercising the pinned runtime/build can establish the end-to-end behavior of the full path.

## Smallest useful GEN-01 extension

Prefer extending the existing relay/OPA unit-test harness rather than adding sleeps or a new standalone harness first.

1. Find the current test fixtures for `OpaEngine`, credentialed endpoint policy, and overlapping L4/L7 endpoints.
2. Add a test-only deterministic barrier immediately before and after `query_endpoint_credential_guards()` in CONNECT setup, without changing production behavior.
3. In the paused window, attempt a policy reload that changes the endpoint from explicit uninspected-credential allowance (P1) to inspected-only (P0), then reverse the direction in a separate case.
4. Assert the engine's lock/reload ordering and generation values explicitly. Do not deadlock by trying to reload while a test deliberately holds the engine mutex inside the query; place barriers outside the locked evaluation or coordinate the query and reload on separate tasks.
5. Assert the CONNECT result and generation guard outcome. For any claim about upstream receipt, run the isolated binary against a local canary that records request/body hashes and only a boolean for the synthetic credential; never log credential values.
6. Run the narrow Rust tests first, then the relevant crate suite. Capture exact commands, exit codes, commit SHA, and logs.

## Decision criteria

- If the barrier cannot expose a valid interleaving because the mutex serializes query and reload, record that as evidence against the hypothesized race, not as a security failure.
- If reload occurs after the credential query, the captured generation guard should make the connection stale before protected relay activity. Verify at the exact call path rather than assuming.
- A unit-test PASS is unit-level evidence only. Keep the upstream-canary scenario separate and NOT TESTED until actually run.

**Current result:** existing source tests and synchronization make a simple mixed-generation race less plausible. No GEN-01 runtime test was executed as part of this audit update; all GEN statuses remain **NOT TESTED**.