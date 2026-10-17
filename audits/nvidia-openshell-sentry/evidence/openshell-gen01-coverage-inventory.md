# GEN-01 coverage inventory — existing tests vs missing evidence

Reviewed source: NVIDIA/OpenShell `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`.
Status: **SOURCE/TEST INVENTORY ONLY — NO TESTS EXECUTED BY THIS AUDIT**.

## Existing source-level coverage found

1. `crates/openshell-supervisor-network/src/proxy/relay.rs` contains `stale_generation_fails_before_relay_context_is_created()`. It captures a decision generation, reloads policy, and asserts relay context is not created. This covers stale generation at relay-context preparation, not upstream receipt during CONNECT setup.
2. `PolicyGenerationGuard` exposes `is_stale()`, `ensure_current()`, and `wait_until_stale()`. The relay uses the watch-based stale signal to terminate inspected and passthrough streams.
3. CONNECT races upstream dialing against `wait_until_stale()` and calls `ensure_current()` after dialing, before sending `200 Connection Established`.
4. `authorize_egress()` captures the generation and evaluates the primary authorization result while holding the engine mutex. `query_endpoint_credential_guards()` also locks the same engine; reload replaces the engine and advances generation under the engine lock.
5. The credential-guard query does not return its own generation. Therefore callers cannot directly compare the guard query's generation to the captured authorization generation using that return value alone. This is a testability/explicit-evidence gap, not proof of a race: engine serialization plus the later CONNECT generation guard may already ensure safe behavior.

Source links:
- [Stale generation relay-context regression test](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy/relay.rs)
- [Generation guard and credential query](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs)
- [CONNECT dial cancellation and final generation check](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs)

## GEN-01 minimal test recommendation

Do not start with a new broad integration harness. First run the existing targeted unit test in a local checkout of the exact pinned commit, then add a deterministic unit-level test for the credential-guard/reload ordering using a test-only barrier or lock-aware seam.

Minimum assertions:
- If the guard query acquires the engine lock before reload, it observes the old engine; if reload acquires it first, it observes the new engine.
- After reload publication, the old `PolicyGenerationGuard` becomes stale and the CONNECT path rejects before returning success.
- No test should infer the credential query's generation from wall-clock order alone; record lock/barrier order and generation values explicitly.
- Add a canary-backed integration test only after the unit-level interleaving is deterministic. Canary must record request/credential presence without logging the secret itself.

## Missing evidence / limitations

- This audit did not build OpenShell or execute Cargo tests.
- The existing relay-context test is not a full CONNECT + upstream-canary test.
- No evidence reviewed here establishes whether the current test suite has a deterministic barrier exactly between credential-guard query completion and the final CONNECT generation check.
- The return type of `query_endpoint_credential_guards()` omits generation, which makes direct assertion of metadata-generation provenance less explicit than for APIs ending in `_with_generation`; do not label this a vulnerability without demonstrating a policy violation.

## Status and disposition

GEN-01 through GEN-04 remain **NOT TESTED** for this audit. The current source evidence reduces the original mixed-generation hypothesis. The next useful action is to execute the existing targeted test in a pinned checkout, then decide whether a new test seam is actually needed.