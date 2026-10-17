# Findings register — OpenShell / Sentry

Date opened: 2026-10-17  
OpenShell source baseline: `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`  
Runtime validation: **not performed in this environment**.

## Summary

| ID | Area | Current assessment | Runtime status |
|---|---|---|---|
| OS-01 | Network paths / direct-egress bypass | Driver-specific isolation mechanisms and named source tests found | NOT TESTED; no bypass reproduced |
| OS-02 | Credential binding / rotation / revocation | E2E source test contract covers endpoint binding and credential rotation/revocation | NOT TESTED |
| OS-06 | Authorization generation and credential guard | Shared authorization snapshot and generation guards found; race remains a falsification hypothesis | NOT TESTED; no vulnerability reproduced |
| OS-07 | Authoritative evaluation errors vs missing L7 metadata | Source regression test distinguishes evaluation error from missing metadata fallback | NOT TESTED |
| OS-08 | VM host bind mounts / virtiofs | Explicit opt-in, source/target validation, RO/RW mode and E2E test contract found; host-side isolation needs further verification | NOT TESTED; no escape reproduced |
| SG-01 | Sentry standalone enforcement and EABC mapping | Evidence not yet collected in this audit | NOT TESTED |
| COM-01 | OpenShell + Sentry composition | Evidence not yet collected; must not infer combined guarantees from component descriptions | NOT TESTED |

## OS-01 — Network paths and direct-egress bypass

**Current assessment:** Driver-specific source mechanisms and test contracts are confirmed. A runtime bypass is not confirmed.

- Docker driver documentation describes `network_mode=none` and TCP/DNS mediation through a seccomp user-notification broker.
- Podman documentation describes `network=none`, protected Unix-socket/authenticated gRPC mediation, and no generic UDP support.
- VM driver documentation describes no virtual NIC and a protected vsock channel.
- Source tests include `workload_sockets_are_bound_to_loopback_and_cannot_be_rebound`, `broker_refuses_socket_families_it_cannot_confine`, `external_connect_waits_for_explicit_relay_decision`, `denied_external_connect_keeps_socket_unconnected`, and `workload_cannot_bind_a_non_loopback_source_address`.

**Limits:** these are source/doc and test-contract findings, not evidence that tests ran. Test each driver independently. Test direct TCP, UDP/DNS, alternate socket APIs, supervisor failure/restart, private/link-local/metadata targets, and DNS rebinding.

## OS-02 — Credential binding, rotation, revocation

**Current assessment:** Source E2E test contract is present; runtime status is NOT TESTED.

Pinned source test: [`stable_external_placeholders.rs`](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/e2e/rust/tests/stable_external_placeholders.rs).

The file is gated by `e2e-docker`. Tests named `persistent_external_placeholder_rotation_and_revocation` and `ordinary_external_placeholder_keeps_revoked_assertion_after_rotation` exercise a synthetic `tools/call` request over a sandbox HTTPS path, endpoint binding controls, and credential rotation/revocation. This is not a complete MCP session or full agent-runtime test. Do not describe it as runtime-passed without a run record.

## OS-06 — Authorization generation / credential guard

**Current assessment:** Source contains generation-pinned authorization and stale-generation checks. The suspected credential-guard/reload race is a test hypothesis, not a confirmed vulnerability.

Reviewed areas include `crates/openshell-supervisor-network/src/proxy.rs`, `opa.rs`, `proxy/relay.rs`, compatibility tests, and RFC 0005. The main authorization result supplies endpoint metadata and generation; the route generation is pinned before credential-guard evaluation; stale generation is checked before upstream connection/CONNECT completion and during dial. Relay paths also check generation and close on fail-closed generation publication.

The separate credential-guard OPA query does not itself return a generation. That fact alone is not a vulnerability because the surrounding route-generation checks may reject stale decisions. RFC text about mixed-generation metadata may be stale relative to implementation; treat as a documentation discrepancy pending reconciliation, not proof of a bug.

**Falsification test:** insert a barrier between primary authorization and credential-guard query; reload policy from a raw-tunnel-allowed rule to a credentialed endpoint requiring L7, and reverse. Also reload between final generation check and CONNECT success and during an active relay. Record whether old-generation traffic reaches upstream. Expected fail-closed result: stale CONNECT rejected/closed before protected upstream bytes flow.

## OS-07 — Evaluation error vs missing L7 metadata

**Current assessment:** Source regression contract is confirmed; runtime is NOT TESTED.

Pinned test file: [`compatibility.rs`](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy/tests/compatibility.rs).

Tests cover missing authorized L7 metadata falling back to L4-only defaults and an authoritative evaluation error denying rather than falling back. This is a useful distinction, but it does not prove every production retrieval/decode failure follows the same fail-closed path.

## OS-08 — VM bind mounts / virtiofs

**Current assessment:** Several source safeguards are confirmed; complete host-path isolation is NOT CONFIRMED. No escape has been reproduced and runtime is NOT TESTED.

Pinned source areas: `crates/openshell-driver-vm/src/driver.rs`, `scripts/openshell-vm-sandbox-init.sh`, `src/ffi.rs`, `README.md`, and `e2e/rust/tests/vm_bind_mount.rs`.

- Bind mounts are opt-in (`enable_bind_mounts` defaults false) and rejected when resource admission is enabled.
- Mount configuration has `read_only` defaulting true; the flag is passed to the libkrun virtiofs API.
- Source path validation checks absolute paths, rejects a final symlink, checks directory/accessibility at provisioning, and fails on missing/inaccessible paths.
- Guest target validation rejects reserved/internal paths and overlaps; guest init refuses symlink target components and fails if mount fails.
- E2E test contract covers two temporary host shares, read/write behavior for RW, and refusal to overwrite through RO.
- OpenShell VM README warns host bind mounts expose host files and may bypass workspace isolation/filesystem policy.

Upstream libkrun documentation warns that virtiofs alone does not isolate a share from other directories/filesystems visible to the host VMM process and recommends host OS mount isolation. This is a material question, not proof that OpenShell is vulnerable: inspect the actual launch environment and verify whether the VMM process is restricted to the intended host paths. Test with harmless canary files outside the allowed share, separately for RO/RW and each supported host platform.

## SG-01 — Sentry standalone

**Status: NOT TESTED / evidence collection pending.** Do not yet infer EABC non-bypassability, boundary integrity, or substrate independence from product positioning. Capture version/commit, deployment requirements, trust boundary, protected effect, attacker model, fail-closed behavior, and evidence for every claim.

## COM-01 — OpenShell + Sentry composition

**Status: NOT TESTED / evidence collection pending.** Establish the exact architecture and path by which protected effects are committed. Determine whether Sentry mediates every path to the effect, how OpenShell policy and Sentry authorization are bound, and what happens on component failure, policy update, bypass path, or downgrade. Component claims must not be added together as if composition were proven.

## References

- OpenShell pinned commit: https://github.com/NVIDIA/OpenShell/commit/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317
- Docker driver: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-docker/README.md
- Podman networking: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-podman/NETWORKING.md
- VM driver README: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/README.md
- libkrun security notes: https://github.com/libkrun/libkrun
