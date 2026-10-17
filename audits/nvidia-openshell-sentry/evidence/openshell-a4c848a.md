# OpenShell source evidence baseline

- Repository: `NVIDIA/OpenShell`
- Commit: `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`
- Commit URL: https://github.com/NVIDIA/OpenShell/commit/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317
- Review method: source/documentation inspection via GitHub connector.
- Local checkout/runtime status: local network resolution for GitHub hosts failed in the review environment; no runtime tests were run as part of this evidence capture.

## OS-01 network mediation

- Docker driver README: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-docker/README.md
- Podman networking: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-podman/NETWORKING.md
- VM driver README: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/README.md
- Socket confinement: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-sandbox/src/linux/socket_confinement.rs
- Network broker: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-sandbox/src/network_broker.rs

Record the distinction between documentation/source mechanism and actual runtime behavior. Test the drivers independently; do not generalize a Docker result to Podman or VM.

## OS-02 credential binding

- E2E source test: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/e2e/rust/tests/stable_external_placeholders.rs
- Named tests include `persistent_external_placeholder_rotation_and_revocation` and `ordinary_external_placeholder_keeps_revoked_assertion_after_rotation`.
- The file is feature-gated for Docker E2E. Source presence is not a record that the test passed.

## OS-06 / OS-07 authorization generation and evaluation failure

- Proxy: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy.rs
- OPA integration: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/opa.rs
- Relay: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy/relay.rs
- Compatibility tests: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy/tests/compatibility.rs
- RFC current shape: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/rfc/0005-sandbox-proxy-egress-adapter/current-shape.md
- RFC implementation plan: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/rfc/0005-sandbox-proxy-egress-adapter/implementation-plan.md

Source review found authorization generation attached to the main decision and multiple stale-generation checks. A separate credential-guard query without its own generation is a race-test lead, not a confirmed vulnerability by itself. The compatibility tests distinguish missing L7 metadata from authoritative evaluation errors; coverage of every production failure mode remains unverified.

## OS-08 VM bind mounts / virtiofs

- VM driver: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/src/driver.rs
- Guest init: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/scripts/openshell-vm-sandbox-init.sh
- libkrun FFI: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/src/ffi.rs
- VM bind-mount E2E: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/e2e/rust/tests/vm_bind_mount.rs
- Upstream libkrun security notes: https://github.com/libkrun/libkrun

Source review found opt-in host mounts, source/target checks, default read-only mode, and a test contract for read-only/read-write behavior. Upstream libkrun warns that virtiofs alone is not a complete host-path isolation boundary from other paths visible to the host VMM process. It remains unconfirmed whether the exact OpenShell launch environment imposes sufficient host-side mount isolation. A canary-file test outside the permitted share is required before making an escape claim.

## Evidence interpretation

This file records source references and reviewer observations, not runtime logs. Runtime artifacts should be added in a separate dated subdirectory or file and linked from the findings register. Keep failed attempts and inconclusive outcomes rather than silently removing them.