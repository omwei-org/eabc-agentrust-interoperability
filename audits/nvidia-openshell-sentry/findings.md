# Findings register — OpenShell / Sentry

Date opened: 2026-10-17  
OpenShell source baseline: `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`  
Runtime validation: **NOT TESTED**. No runtime reproduction attempts were performed in this audit. This register assesses only the pinned commit below; upstream drift is recorded separately as BASELINE-01.

## Summary

| ID | Area | Evidence class | EABC criterion | Current assessment | Test status |
|---|---|---|---|---|---|
| BASELINE-01 | Upstream source baseline drift | SOURCE | NON_BYPASSABILITY(B,E); INTEGRITY_DEF(B); INTEGRITY_STATE(B,E); INTEGRITY_CTX(C,B,E) | Current upstream has material isolation-interface and conformance-harness changes; no claim that those changes are vulnerabilities or regressions | NOT TESTED — newer baseline not audited |
| BASELINE-02 | Explicit outer-fence guarantee contract replaced by opaque provisioning evidence | SOURCE | NON_BYPASSABILITY(B,E); INTEGRITY_STATE(B,E); INTEGRITY_CTX(C,B,E) | The common contract no longer requires explicit normalized guarantees for default-deny, no unmanaged egress, revocation and controller-loss fail-closed; driver/native evidence must be reviewed for equivalent enforcement | NOT TESTED — assurance-contract change, runtime effect unknown |
| OS-01 | Network paths / direct-egress bypass | DOC-CLAIM + SOURCE + TEST-CONTRACT | NON_BYPASSABILITY(B,E); INTEGRITY_CTX(C,B,E) | Driver-specific controls and named tests identified; runtime behavior unknown | NOT TESTED — runtime bypass status unknown |
| OS-02 | Credential binding / rotation / revocation | TEST-CONTRACT | INTEGRITY_CTX(C,B,E); EXCLUSIVITY; NON_BYPASSABILITY(B,E) | E2E source test contract covers endpoint binding and credential rotation/revocation | NOT TESTED — source test contract only |
| OS-06 | Authorization generation and credential guard | SOURCE + TEST-CONTRACT + DOC-CLAIM | INTEGRITY_STATE(B,E); INTEGRITY_CTX(C,B,E); NON_BYPASSABILITY(B,E) | Generation guards found; race and RFC/implementation discrepancy remain unresolved | NOT TESTED — race hypothesis not validated |
| OS-07 | Evaluation errors vs missing L7 metadata | TEST-CONTRACT + SOURCE | INTEGRITY_CTX(C,B,E); EXCLUSIVITY; NON_BYPASSABILITY(B,E) | Regression contract distinguishes evaluation errors from missing-metadata fallback; fallback safety remains open | NOT TESTED — source regression contract only |
| OS-08 | VM host bind mounts / virtiofs | DOC-CLAIM + SOURCE + TEST-CONTRACT | NON_BYPASSABILITY(B,E); INTEGRITY_DEF(B); INTEGRITY_CTX(C,B,E) | Several controls identified; complete host-path isolation unverified | NOT TESTED — host-path escape status unknown |
| SG-01 | Sentry standalone enforcement | NOT ASSESSED | To be determined from concrete protected effect and boundary | Evidence not yet collected | NOT TESTED — evidence collection pending |
| COM-01 | OpenShell + Sentry composition | NOT ASSESSED | To be determined for the composed enforcement boundary | Evidence not yet collected; do not infer composition guarantees from component claims | NOT TESTED — integration evidence pending |

## BASELINE-02 — Outer-fence assurance contract changed

**Evidence class:** `SOURCE`. **Status: NOT TESTED — assurance-contract change, runtime effect unknown.** This is a concrete source-level difference between the pinned audit baseline and the checked newer upstream commit. It is not, by itself, proof of a runtime vulnerability.

At the pinned baseline, `OuterFenceGuarantees::validate` required the exact set `DefaultDenyEgress`, `NoUnmanagedEgressPath`, `RevocationVerified`, and `ControllerLossFailsClosed` for the admitted generation ([old contract, lines 389–469](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-isolation-interface/src/contract.rs#L389-L469)). At the checked newer upstream commit, this common guarantee set is replaced by `ProvisioningEvidence`, which binds native evidence to a generation and explicitly says the digest is not independent proof of policy enforcement ([new contract, lines 219–293](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-isolation-interface/src/contract.rs#L219-L293)). The Docker projection itself checks non-empty container ID, `network_mode == "none"`, and no unexpected networks before creating the evidence digest ([Docker isolation, lines 25–60](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-docker/src/isolation.rs#L25-L60)). Importantly, Docker also inspects the actual container configuration and attached networks and rejects drift ([Docker outer-fence inspection, lines 3082–3110](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-docker/src/lib.rs#L3082-L3110)). Podman likewise inspects the actual container and rejects a non-`none` network mode, privileged mode, or attached network ([Podman fence verification, lines 564–595](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-podman/src/client.rs#L564-L595)); its launch and restart paths call this check before starting the workload ([launch path, lines 1536–1546](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-podman/src/driver.rs#L1536-L1546), [restart path, lines 1636–1644](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-podman/src/driver.rs#L1636-L1644)). The common runtime validates generation, session, resource claims and evidence-digest equality before proceeding, and validates native audit schema only for its built-in backend ([runtime confirmation, lines 357–389](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-sandbox-backend/src/runtime.rs#L357-L389)). A delegated-backend test intentionally accepts `backend_audit = null` and proceeds to `start_agent` ([delegated runtime test, lines 81–101](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-sandbox-backend/src/runtime/tests/delegated.rs#L81-L101)).

**Interpretation:** the newer design may deliberately move enforcement-specific validation into trusted driver/backend code. Therefore, the removal of common normalized guarantees is not enough to claim a regression. But the old common interface's explicit four-property check is no longer present at this layer. We need evidence showing where each equivalent guarantee is now established, validated, and maintained through runtime failure and policy change.

**EABC relevance:** `NON_BYPASSABILITY(B,E)` requires evidence that all paths to the protected effect traverse enforcement; `INTEGRITY_STATE(B,E)` requires evidence for revocation and controller-loss transitions where applicable; `INTEGRITY_CTX(C,B,E)` requires binding of the admitted generation/session/identity/policy to the actual enforcement state. An evidence digest binds bytes to a generation; it does not itself prove the truth or completeness of the claims represented by those bytes.

**Falsification / verification plan:** for Docker, Podman and VM independently, inspect the trusted native validation path and test default-deny, attempted unmanaged egress, revocation of previously allowed traffic, and controller/broker loss. Use an upstream canary that records whether any protected bytes arrive. Include built-in and delegated backends, including missing, empty, malformed and semantically incomplete audit evidence. Record whether launch is refused and whether active traffic is closed; do not treat digest equality or successful startup alone as proof.

## BASELINE-01 — Upstream source baseline drift

**Evidence class:** `SOURCE`. **Status: NOT TESTED — newer baseline not audited.**

**Observation:** The audit baseline is pinned to `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`. At the time of this check, NVIDIA/OpenShell `main` was `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`, 13 commits ahead of the pinned baseline. The comparison reports 225 changed files across the full repository. This does not automatically invalidate commit-specific observations, but it means they must not be presented as an audit of current `main`.

**Relevant changed surfaces:** `crates/openshell-isolation-interface/src/contract.rs` changed from 1,076 to 626 lines and now describes validated data shared by an RPC client/server rather than the earlier runtime-selectable trait contract; `crates/openshell-isolation-interface/tests/backend_conformance.rs` changed from 907 to 140 lines, with its header now describing shared-data validation and lifecycle/process behavior tested over RPC. Driver isolation modules and network-recovery tests also changed. These are architectural/test-harness changes to review, not proof that coverage or enforcement weakened; test coverage may have moved to other files.

**EABC relevance:** Re-audit the concrete enforcement boundary and substrate before making claims about `NON_BYPASSABILITY(B,E)`, `INTEGRITY_DEF(B)`, `INTEGRITY_STATE(B,E)`, or `INTEGRITY_CTX(C,B,E)`. A conformance harness change is not itself evidence of EABC conformance or non-conformance.

**Pinned comparison evidence:** [baseline commit](https://github.com/NVIDIA/OpenShell/commit/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317); [checked upstream commit](https://github.com/NVIDIA/OpenShell/commit/b58e24c9dabd6d4bcf2b7186592d3ad50646541b); [compare the 13-commit range](https://github.com/NVIDIA/OpenShell/compare/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317...b58e24c9dabd6d4bcf2b7186592d3ad50646541b); [isolation contract at checked upstream commit](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-isolation-interface/src/contract.rs); [backend conformance tests at checked upstream commit](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-isolation-interface/tests/backend_conformance.rs).

**Next step:** keep the current findings explicitly commit-scoped. Add a follow-up review of the changed isolation interface, RPC protocol, replacement conformance tests, driver implementations and network recovery behavior before making any claim about current upstream `main`. Do not silently move the pinned baseline.

---

## OS-01 — Network paths and direct-egress bypass

**Evidence classes:** `DOC-CLAIM` for driver documentation; `SOURCE` for inspected implementation; `TEST-CONTRACT` for named tests. **Runtime status: NOT TESTED — runtime bypass status unknown.**

**EABC relevance:** Primarily `NON_BYPASSABILITY(B,E)` for every path to the protected effect, plus `INTEGRITY_CTX(C,B,E)` where routing/endpoint context determines authorization. This is a candidate mapping, not an EABC conformance result.

- Docker driver documentation describes `network_mode=none` and TCP/DNS mediation through a seccomp user-notification broker.
- Podman documentation describes `network=none`, protected Unix-socket/authenticated gRPC mediation, and no generic UDP support.
- VM driver documentation describes no virtual NIC and a protected vsock channel.
- Source tests include `workload_sockets_are_bound_to_loopback_and_cannot_be_rebound`, `broker_refuses_socket_families_it_cannot_confine`, `external_connect_waits_for_explicit_relay_decision`, `denied_external_connect_keeps_socket_unconnected`, and `workload_cannot_bind_a_non_loopback_source_address`.

**Limits:** These are documentation/source/test-contract observations, not evidence that tests ran. Test each driver independently. Test direct TCP, UDP, IPv6, ICMP, raw sockets, UNIX socket paths outside the broker, supervisor failure/restart, private/link-local/metadata targets, and DNS rebinding including mixed A/AAAA answers.

**Pinned evidence:** [Docker driver README, lines 39–44](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-docker/README.md#L39-L44); [Podman networking, lines 1–25](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-podman/NETWORKING.md#L1-L25); [VM driver README, lines 281–286](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/README.md#L281-L286); [network broker tests, lines 2603–2690 and 2898–3005](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-sandbox/src/network_broker.rs#L2603-L2690) and [network broker connect tests](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-sandbox/src/network_broker.rs#L2898-L3005).

## OS-02 — Credential binding, rotation, revocation

**Evidence class:** `TEST-CONTRACT` (source test inspected). **Runtime status: NOT TESTED — source test contract only.**

**EABC relevance:** `INTEGRITY_CTX(C,B,E)` for endpoint/credential binding, `EXCLUSIVITY` for preventing use outside the authorized endpoint, and `NON_BYPASSABILITY(B,E)` only if all paths to the protected effect are mediated. The test contract alone does not establish those EABC properties.

Pinned source test: [`stable_external_placeholders.rs`, lines 1028–1043](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/e2e/rust/tests/stable_external_placeholders.rs#L1028-L1043).

The file is gated by `e2e-docker`. Tests named `persistent_external_placeholder_rotation_and_revocation` and `ordinary_external_placeholder_keeps_revoked_assertion_after_rotation` exercise a synthetic `tools/call` request over a sandbox HTTPS path, endpoint binding controls, and credential rotation/revocation. This is not a complete MCP session or full agent-runtime test. Do not describe it as runtime-passed without a run record. [Pinned test functions, lines 1028–1043](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/e2e/rust/tests/stable_external_placeholders.rs#L1028-L1043).

## OS-06 — Authorization generation / credential guard

**Evidence classes:** `SOURCE` and `TEST-CONTRACT`; RFC claims are `DOC-CLAIM`. **Runtime status: NOT TESTED — race hypothesis not validated.**

**EABC relevance:** `INTEGRITY_STATE(B,E)` and `INTEGRITY_CTX(C,B,E)` because policy generation and endpoint context must remain bound to the decision; `NON_BYPASSABILITY(B,E)` if a stale decision can reach the protected effect. These are audit mappings, not conformance conclusions.

Reviewed areas include `crates/openshell-supervisor-network/src/proxy.rs`, `opa.rs`, `proxy/relay.rs`, compatibility tests, and RFC 0005. The main authorization result supplies endpoint metadata and generation; the route generation is pinned before credential-guard evaluation; stale generation is checked before upstream connection/CONNECT completion and during dial. Relay paths also check generation and close on fail-closed generation publication.

The separate credential-guard OPA query does not itself return a generation. That fact alone is not a vulnerability because the surrounding route-generation checks may reject stale decisions. There is an unresolved documentation/implementation discrepancy: [RFC 0005 current-shape, lines 221–240](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/rfc/0005-sandbox-proxy-egress-adapter/current-shape.md#L221-L240) describes sibling metadata queries not all asserted against the L4 decision generation, while [the implementation plan, lines 66–82](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/rfc/0005-sandbox-proxy-egress-adapter/implementation-plan.md#L66-L82) describes generation-consistent authorization cutover. Reconcile these statements against the exact implementation before classifying either as stale. This discrepancy is not proof of a vulnerability.

**Pinned implementation evidence:** [proxy generation handling, lines 730–770](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy.rs#L730-L770); [OPA generation guard definitions, lines 180–225](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/opa.rs#L180-L225); [relay generation validation, lines 95–145](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy/relay.rs#L95-L145).

**Falsification test:** insert a barrier between primary authorization and credential-guard query; reload policy from a raw-tunnel-allowed rule to a credentialed endpoint requiring L7, and reverse. Also reload between final generation check and CONNECT success and during an active relay. Record whether old-generation traffic reaches upstream. Expected fail-closed result: stale CONNECT rejected/closed before protected upstream bytes flow.

## OS-07 — Evaluation error vs missing L7 metadata

**Evidence class:** `TEST-CONTRACT` (source regression tests inspected). **Runtime status: NOT TESTED — source regression contract only.**

**EABC relevance:** `INTEGRITY_CTX(C,B,E)` and `NON_BYPASSABILITY(B,E)`: a fallback must not silently weaken the boundary applicable to the protected effect.

Pinned test file: [`compatibility.rs`, lines 283–330](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy/tests/compatibility.rs#L283-L330).

Tests cover missing authorized L7 metadata falling back to L4-only defaults and an authoritative evaluation error denying rather than falling back. This is a useful distinction, but it does not prove every production retrieval/decode failure follows the same fail-closed path. More importantly, the L4-only fallback itself needs risk assessment for endpoints using credential injection: determine whether the weaker L4 decision can still permit a protected request or expose injected credentials when L7 metadata is missing. [Pinned compatibility tests, lines 270–345](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-supervisor-network/src/proxy/tests/compatibility.rs#L270-L345).

## OS-08 — VM bind mounts / virtiofs

**Evidence classes:** `DOC-CLAIM`, `SOURCE`, and `TEST-CONTRACT`. **Runtime status: NOT TESTED — host-path escape status unknown.**

**EABC relevance:** `NON_BYPASSABILITY(B,E)` and `INTEGRITY_DEF(B)` for the filesystem boundary; `INTEGRITY_CTX(C,B,E)` where the configured share defines the authorized context.

Pinned source areas: `crates/openshell-driver-vm/src/driver.rs`, `scripts/openshell-vm-sandbox-init.sh`, `src/ffi.rs`, `README.md`, and `e2e/rust/tests/vm_bind_mount.rs`.

- Bind mounts are opt-in (`enable_bind_mounts` defaults false) and rejected when resource admission is enabled.
- Mount configuration has `read_only` defaulting true; the flag is passed to the libkrun virtiofs API.
- Source path validation checks absolute paths, rejects a final symlink, checks directory/accessibility at provisioning, and fails on missing/inaccessible paths.
- Guest target validation rejects reserved/internal paths and overlaps; guest init refuses symlink target components and fails if mount fails.
- E2E test contract covers two temporary host shares, read/write behavior for RW, and refusal to overwrite through RO.
- OpenShell VM README warns host bind mounts expose host files and may bypass workspace isolation/filesystem policy.

Upstream libkrun documentation warns that virtiofs alone does not isolate a share from other directories/filesystems visible to the host VMM process and recommends host OS mount isolation. This is a material question, not proof that OpenShell is vulnerable: inspect the actual launch environment and verify whether the VMM process is restricted to the intended host paths. Test with harmless canary files outside the allowed share, separately for RO/RW and each supported host platform. Also test symlinks and hardlinks inside the shared tree that target outside paths, `..` traversal, and already-open file descriptors; determine whether the host VMM process or guest can follow those paths. [VM read-only default, lines 140–160](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/src/driver.rs#L140-L160); [bind-mount opt-in and validation, lines 5150–5165](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/src/driver.rs#L5150-L5165); [guest virtiofs target checks, lines 526–585](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/scripts/openshell-vm-sandbox-init.sh#L526-L585); [VM bind-mount E2E test, lines 1–100](https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/e2e/rust/tests/vm_bind_mount.rs#L1-L100).

## SG-01 — Sentry standalone

**Evidence class:** `DOC-CLAIM` for NVIDIA's public architecture/capability statements; `SOURCE` and `RUNTIME` not assessed. **Status: NOT TESTED — implementation and enforcement evidence pending.** NVIDIA describes Sentry as an out-of-band watchdog on BlueField-4, with in-silicon policy enforcement, agent monitoring, attested telemetry, identity verification and quarantine when an agent moves outside its software boundary ([official NVIDIA announcement, 28 Sep 2026](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Launches-Open-Agent-Safety-Platform-to-Secure-Agents-From-Testing-to-Deployment/), lines 117–121). These are vendor claims, not independently verified behavior or an EABC conformance result.

**Candidate EABC criteria, not yet established:** `NON_BYPASSABILITY(B,E)` requires proof that every path to the concrete protected effect traverses the boundary; `INTEGRITY_CTX(C,B,E)` requires binding of identity, policy, target and request context; `INTEGRITY_STATE(B,E)` may apply to policy/version freshness and fail-safe state transitions; `ENFORCEMENT_INDEPENDENCE` is an EBP assurance constraint, not an EABC semantic property. Do not mark any of these satisfied based on the announcement alone. Before testing, pin exact Sentry software/firmware version, device model, deployment mode and configuration; specify the protected effect, attacker model, trust boundary, failure behavior and observable evidence.

## COM-01 — OpenShell + Sentry composition

**Evidence class:** `DOC-CLAIM` for the platform description; integrated `SOURCE` and `RUNTIME` not assessed. **Status: NOT TESTED — integration evidence pending.** NVIDIA describes OpenShell as the software runtime boundary and Sentry/BlueField-4 as an additional out-of-band hardware layer ([official NVIDIA announcement](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Launches-Open-Agent-Safety-Platform-to-Secure-Agents-From-Testing-to-Deployment/), lines 117–121). The announcement does not establish how authorization is bound across the two components or prove that all protected-effect commit paths are mediated.

**Candidate EABC criteria, not yet established:** `NON_BYPASSABILITY(B,E)` for the composed boundary; `INTEGRITY_CTX(C,B,E)` for binding OpenShell policy, Sentry identity/decision and the actual target/request; `INTEGRITY_STATE(B,E)` for policy updates, reset, downgrade and component failure. Before testing, pin OpenShell commit plus exact Sentry software/firmware, device and configuration. Enumerate alternate/local paths to the protected effect, then test authorized/denied actions, failure, restart, policy changes, stale decisions and downgrade. Component claims must not be added together as if composition were proven.

## References

- OpenShell pinned commit: https://github.com/NVIDIA/OpenShell/commit/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317
- Docker driver: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-docker/README.md
- Podman networking: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-podman/NETWORKING.md
- VM driver README: https://github.com/NVIDIA/OpenShell/blob/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317/crates/openshell-driver-vm/README.md
- libkrun security notes: https://github.com/libkrun/libkrun (upstream documentation; pin the exact reviewed revision before treating it as a reproducible evidence artifact)
