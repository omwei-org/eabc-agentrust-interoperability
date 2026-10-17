# OpenShell revocation and controller-loss evidence review

Review date: 2026-10-17  
Source commit: `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`  
Original comparison baseline: `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`  
Status: **SOURCE REVIEW ONLY — runtime tests NOT TESTED. No confirmed vulnerability claimed.**

## Question

The old isolation contract required `RevocationVerified` and `ControllerLossFailsClosed` in the common outer-fence guarantee set. The newer contract uses generation-bound `ProvisioningEvidence`. This review asks whether the corresponding guarantees can be traced to the new contract, common runtime, and concrete backend paths.

## Evidence found

### 1. The new isolation-backend RFC retains a normative loss requirement

RFC 0012, at the pinned source commit, states that if the logical supervisor or its transport is lost, enforcement must remain in force and supervisor-dependent operations fail closed. Network-mediation unavailability must deny outbound connections without enabling direct egress. If required enforcement cannot be maintained, a backend or trusted node/control-plane actor must stop workload execution within a documented bound. Each backend is expected to document its behavior and bound. Transport recovery is scoped to the same logical supervisor process; a replacement supervisor cannot resume an existing generation with launch credentials.

Source: [RFC 0012 failure and loss invariants, lines 95–110](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0012-isolation-backend/README.md#L95-L110) and [failure semantics, lines 345–390](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/rfc/0012-isolation-backend/README.md#L345-L390).

**Interpretation:** controller/supervisor-loss semantics were not simply removed from the architecture-level requirements. The open issue is whether every admitted backend and deployment path implements and tests the normative requirement, with a concrete stopping bound.

### 2. Credential revocation has implementation evidence, but it is narrower than whole-boundary revocation

The supervisor runtime has an explicit failure path that revokes static provider credentials when the requested provider environment cannot be obtained or its bindings fail validation. The source comments explicitly say previous dynamic grants may remain active; therefore this must not be described as revocation of every credential class.

Sources:
- [provider environment failure revocation, lines 791–812](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor/src/config_runtime.rs#L791-L812)
- [binding validation/revocation, lines 818–840](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor/src/config_runtime.rs#L818-L840)
- [provider expiry and stale-placeholder behavior, lines 786–800](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/docs/how-it-works/providers/profiles.mdx#L786-L800)

This supports a narrower statement about static provider credential handling. It does **not** by itself establish that a sandbox's complete policy is revoked, that all active network connections are closed, or that an untrusted workload stops when required enforcement is lost.

### 3. Boundary transport and mediation have lifecycle handling

The sandbox boundary runtime tracks control connections and connection expiry. Its persistent mediation path terminates the mediation task when the reader, writer, or broker-accept task completes; this is source evidence that the mediation stream has a lifecycle, not proof that every backend prevents all network effects after transport loss.

Sources:
- [boundary control connection lifecycle, lines 587–637](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-sandbox/src/boundary_server.rs#L587-L637)
- [persistent mediation task lifecycle, lines 1010–1105](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-sandbox/src/boundary_server.rs#L1010-L1105)

The host-VM supervisor also supports parent-liveness stdin: the driver closing the liveness pipe or exiting causes the supervisor process to terminate. This is a process-lifecycle mechanism, but the full chain from supervisor termination to workload termination and outer-fence preservation must be traced and tested separately.

Source: [supervisor README: parent-liveness stdin](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor/README.md).

## Evidence gap by claim

| Claim | Source evidence currently found | Still needed |
|---|---|---|
| Static provider credential revocation on failed refresh/binding | Supervisor code revokes static provider environment; docs describe stale/expired placeholders failing closed | Exact-SHA test of old static placeholder after update/revocation; verify all request paths reject and no secret reaches a canary |
| General policy revocation for a running sandbox | Policy generation and stale-state handling exist in the supervisor/network code; this review has not closed every affected operation and backend path | Trace policy update through generation change to active connection closure and protected-effect denial, per backend |
| Controller/supervisor transport loss | RFC 0012 normatively requires continued enforcement, fail-closed supervisor operations and bounded stop if enforcement cannot be maintained; boundary transport/mediation lifecycle code exists | Per-backend loss path, exact bound, recovery semantics, and effect-side test while workload is actively attempting egress |
| Trusted cleanup when backend cleanup is unavailable | RFC 0012 requires a trusted driver cleanup path | Evidence for each supported driver and a test that workload cannot continue after loss |
| Replacement supervisor / stale generation | RFC 0012 says replacement process cannot resume the existing generation with launch credentials; runtime binds generation/session/evidence | Exact-SHA regression test covering replacement supervisor and old credentials against active and restarted resources |

## Required next tests

1. **Credential revocation:** create an endpoint-bound static credential, prove it works, revoke/change its binding, wait for the declared activation boundary, then attempt the old placeholder against an instrumented canary. Record policy generation, request decision and whether any protected bytes arrive.
2. **Controller/transport loss:** run a workload that repeatedly attempts harmless egress to a recording canary; sever the supervisor-to-boundary transport and separately terminate the logical supervisor. Record whether egress is denied immediately, whether the workload is paused/terminated/contained, and the measured bound until termination where applicable.
3. **Backend matrix:** repeat for Docker, Podman, QEMU/libkrun and Kubernetes where supported. Do not generalize one backend's behavior to another.
4. **Recovery/replacement:** reconnect the same logical supervisor, then separately try a replacement supervisor and old generation credentials. Confirm no prior generation resumes without fresh admission/binding.
5. Capture exact SHA, commands, test names, exit codes, logs and canary-side observations. Until then, status remains **NOT TESTED**.

## EABC interpretation

Candidate mapping only, pending comparison with the canonical EABC specification:
- `INTEGRITY_STATE(B,E)`: revocation and loss/recovery transitions.
- `INTEGRITY_CTX(C,B,E)`: binding the active generation/session to the enforcement instance.
- `NON_BYPASSABILITY(B,E)`: proving that network mediation or a trusted stop path remains effective during loss.

No runtime PASS/FAIL is assigned in this source review. The overall audit verdict remains **INCONCLUSIVE**.
