# OpenShell source and documentation evidence baseline

- Repository: `NVIDIA/OpenShell`
- Pinned commit: `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`
- Commit permalink: https://github.com/NVIDIA/OpenShell/commit/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317
- Review method: inspection of pinned source, repository documentation and source test contracts through GitHub repository access.
- Runtime status: **NOT TESTED**. Local checkout/runtime testing was not performed because GitHub host resolution failed in the review environment.
- Evidence-class rule: documentation statements are `DOC-CLAIM`; implementation observations are `SOURCE`; named test assertions are `TEST-CONTRACT`; only executed tests with reproducible artifacts are `RUNTIME`.

These references document what was inspected. They do not establish that a test ran, that the control is effective under an adversarial runtime, or that OpenShell conforms to EABC.

## OS-01 — Network mediation

### Documentation claims (`DOC-CLAIM`)

- Docker driver README, networking discussion: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-docker/README.md#L35-L49
- Podman networking documentation: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-podman/NETWORKING.md#L1-L25
- VM driver README, architecture/networking context: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/README.md#L1-L65

### Implementation and test-contract references (`SOURCE` / `TEST-CONTRACT`)

- Socket confinement implementation: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-sandbox/src/linux/socket_confinement.rs#L150-L210
- Network broker tests for non-loopback binding, explicit relay decision and denied connection: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-sandbox/src/network_broker.rs#L2880-L3010

**Interpretation:** Driver documentation and source test contracts were inspected. No runtime bypass test was performed. Docker, Podman and VM must be assessed independently; do not generalize a result across drivers.

## OS-02 — Credential binding, rotation and revocation

- Pinned E2E source test (`TEST-CONTRACT`): https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/e2e/rust/tests/stable_external_placeholders.rs#L1020-L1105
- Named tests include `persistent_external_placeholder_rotation_and_revocation` and `ordinary_external_placeholder_keeps_revoked_assertion_after_rotation`.

The test file is feature-gated for Docker E2E. The source contract uses synthetic endpoint behavior and generation/counter assertions. It is not a full MCP session or full agent-runtime test. Source presence is not a run record.

## OS-06 — Authorization generation and credential guard

### Implementation (`SOURCE`)

- Proxy generation handling: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy.rs#L730-L770
- OPA generation-guard definitions: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/opa.rs#L180-L225
- Relay generation validation: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy/relay.rs#L95-L145

### Tests and documentation (`TEST-CONTRACT` / `DOC-CLAIM`)

- Compatibility tests: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy/tests/compatibility.rs#L270-L345
- RFC 0005 current-shape: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/rfc/0005-sandbox-proxy-egress-adapter/current-shape.md#L221-L240
- RFC 0005 implementation plan: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/rfc/0005-sandbox-proxy-egress-adapter/implementation-plan.md#L66-L82

**Unresolved documentation/implementation discrepancy:** current-shape describes sibling metadata queries not all being asserted against the L4 decision generation; the implementation plan describes generation-consistent authorization cutover. These statements must be reconciled against the pinned implementation. Do not label the RFC stale until that comparison is completed. This discrepancy alone is not proof of a vulnerability.

A credential-guard query without its own generation is a race-test lead, not a confirmed vulnerability by itself. Runtime race tests have not been performed.

## OS-07 — Evaluation error versus missing L7 metadata

- Pinned compatibility tests (`TEST-CONTRACT`): https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy/tests/compatibility.rs#L270-L345
- `missing_authorized_l7_metadata_preserves_l4_only_fallback`
- `authoritative_evaluation_error_denies_without_metadata_fallback`

The source tests distinguish a missing-metadata compatibility fallback from an authoritative evaluation error. Runtime status is **NOT TESTED**. The safety of L4-only fallback needs separate assessment for credential-injection endpoints: determine whether the weaker decision can permit a protected request or expose injected credentials.

## OS-08 — VM bind mounts and virtiofs

### Implementation and test contract (`SOURCE` / `TEST-CONTRACT`)

- VM mount configuration and `read_only` defaults: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/src/driver.rs#L120-L160
- Guest virtiofs target checks: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/scripts/openshell-vm-sandbox-init.sh#L520-L565
- libkrun FFI surface: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/src/ffi.rs#L25-L75
- VM bind-mount E2E test: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/e2e/rust/tests/vm_bind_mount.rs#L1-L100
- VM driver documentation, mount configuration: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/README.md#L165-L200

### Upstream documentation claim (`DOC-CLAIM`)

- libkrun repository/security notes: https://github.com/libkrun/libkrun

The upstream documentation raises a host-side isolation question for paths visible to the VMM process. The exact reviewed upstream revision should be pinned before using it as a reproducible evidence artifact. This is not proof that OpenShell is vulnerable.

The current E2E source contract does not cover in-share symlinks/hardlinks targeting outside paths, `..` traversal, or already-open file descriptors. Runtime host-path isolation remains unverified. Add harmless canary-file tests outside the permitted share and capture both guest behavior and host/VMM-side evidence.

## SG-01 — Sentry standalone

Evidence collection is pending. No Sentry version has yet been pinned. Before making claims, record the exact software/firmware version, device/model, deployment mode and configuration. Then establish the protected effect, all commit paths, attacker model, fail-closed behavior and relevant EABC criteria. Status: **NOT TESTED**.

## COM-01 — OpenShell + Sentry composition

Integration evidence collection is pending. Pin the OpenShell commit plus exact Sentry software/firmware version, device/model, deployment mode and configuration. Establish the actual commit path for the protected effect and test failure, policy change, alternate path and downgrade cases. Do not infer composition guarantees from individual component claims. Status: **NOT TESTED**.


## Sentry and composition — public claims only

- Official NVIDIA announcement, published 28 September 2026: https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Launches-Open-Agent-Safety-Platform-to-Secure-Agents-From-Testing-to-Deployment/
- Relevant announcement passage: https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Launches-Open-Agent-Safety-Platform-to-Secure-Agents-From-Testing-to-Deployment/ (description of OpenShell as software runtime boundary and Sentry/BlueField-4 as an out-of-band hardware layer; announcement lines 117–121).

**Evidence class: `DOC-CLAIM` only.** This is NVIDIA's description of intended architecture and capabilities. It does not establish the behavior of a particular firmware/software release, prove all paths to a protected effect are mediated, or show conformance to EABC.

### Candidate EABC mapping — unverified

- `NON_BYPASSABILITY(B,E)`: must identify the concrete protected effect and enumerate every commit path, including local/alternate paths; vendor positioning does not prove complete mediation.
- `INTEGRITY_CTX(C,B,E)`: must demonstrate binding among requester/agent identity, policy decision, target, request context and the actual protected effect.
- `INTEGRITY_STATE(B,E)`: test stale authorization, policy update, reset, downgrade and component failure if these can affect boundary satisfaction.
- `ENFORCEMENT_INDEPENDENCE` is an EBP assurance constraint, not an EABC semantic property; it requires evidence about the enforcement path's independence from the compromised software under the declared adversary model.

No exact Sentry firmware/software version, device configuration, or integrated runtime evidence has been pinned in this audit. Sentry standalone and OpenShell+Sentry composition remain `NOT TESTED`.

## Evidence interpretation

This file records pinned references and reviewer observations, not runtime logs. Add execution records separately with date, environment, exact commands, versions/configuration, observed client-side and effect-side results, artifacts, and status (`PASS`, `FAIL`, or `INCONCLUSIVE`). Keep failed and inconclusive attempts. Do not mark a test as run based on the presence of source code alone.
