# OpenShell follow-up source review — b58e24c

## Review identity

- Repository: [NVIDIA/OpenShell](https://github.com/NVIDIA/OpenShell)
- Checked commit: [`b58e24c9dabd6d4bcf2b7186592d3ad50646541b`](https://github.com/NVIDIA/OpenShell/commit/b58e24c9dabd6d4bcf2b7186592d3ad50646541b)
- Commit message: `fix(supervisor): report plaintext scheme to middleware (#4397)`
- Committer timestamp: 2026-10-17T01:38:03Z
- Review type: targeted source/documentation inspection through GitHub repository access
- Runtime validation: **NOT TESTED**. No runtime commands, integration tests or bypass attempts were executed.
- Scope: targeted follow-up for OS-06, OS-09, BASELINE-02 through BASELINE-04. This is not a complete re-audit of all changed files or of every driver.

## OS-06 — generation guards and stale relay

**Evidence class: SOURCE + TEST-CONTRACT.**

- [Generation guard implementation, `opa.rs` lines 206–249](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L206-L249): captures the expected generation, rejects a mismatch and exposes a current-generation check/wait path.
- [CONNECT setup checks, `proxy.rs` lines 2947–2999](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2947-L2999): checks staleness around upstream connection establishment and before returning CONNECT success.
- [Stale relay test, `proxy.rs` lines 14100–14150](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L14100-L14150): source test asserts a stale forward relay writes no bytes to upstream.

**Limit:** these source controls/tests are not evidence that the tests were executed here, that all metadata was materialized from one generation, or that every race window is covered. Runtime status remains NOT TESTED.

## OS-09 — L4 fallback and credential guard counter-evidence

**Evidence class: SOURCE + TEST-CONTRACT + DOC-CLAIM.**

- [CONNECT credential guard decision, `proxy.rs` lines 2899–2944](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L2899-L2944): provider-credentialed endpoints are rejected when uninspected credentials are not explicitly allowed.
- [Credential-guard aggregation, `proxy.rs` lines 4008–4054](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/proxy.rs#L4008-L4054).
- [OPA regression test, `opa.rs` lines 9612–9690](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor-network/src/opa.rs#L9612-L9690): tests that an L4-only credentialed endpoint does not shadow the inspected endpoint's TLS/SSRF configuration.
- [Current provider profile documentation](https://docs.nvidia.com/openshell/dev/how-it-works/providers/profiles): documents host/port/path binding and separates credential binding from network-policy authorization.

**Interpretation:** this is counter-evidence against treating L4 fallback alone as a confirmed vulnerability. It does not replace end-to-end testing for missing/malformed metadata, overlapping endpoints, policy reloads or the explicit opt-in path. Runtime status remains NOT TESTED.

## BASELINE-02 / BASELINE-03 — native enforcement evidence

- [Current common provisioning-evidence contract, `contract.rs` lines 219–293](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-isolation-interface/src/contract.rs#L219-L293): binds native evidence to a generation and warns that a digest is not independent proof of enforcement.
- [Docker isolation projection, `isolation.rs` lines 25–60](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-docker/src/isolation.rs#L25-L60) and [actual Docker outer-fence inspection, `lib.rs` lines 3082–3110](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-docker/src/lib.rs#L3082-L3110).
- [Podman fence verification, `client.rs` lines 564–595](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-podman/src/client.rs#L564-L595).
- [VM launch arguments, `runtime.rs` lines 121–150 and 188–190](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-vm/src/runtime.rs#L121-L150): QEMU launch includes `-nic none`.
- [libkrun launch, `runtime.rs` lines 320–354](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-driver-vm/src/runtime.rs#L320-L354): describes the vsock/virtiofs device setup and no network helper.

**Interpretation:** these are useful source-level controls, not runtime proof. A fixed evidence field or matching digest does not alone prove actual enforcement; conversely, the inspected launch/inspection code is counter-evidence against asserting a defect solely from the evidence representation.

## BASELINE-04 — delegated backend trust boundary

- [Backend selection and admission, `backend_setup.rs` lines 51–140](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor/src/backend_setup.rs#L51-L140).
- [Registration tests, `backend_setup/tests.rs` lines 37–109](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor/src/backend_setup/tests.rs#L37-L109) and [admission rejection test, lines 387–416](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-supervisor/src/backend_setup/tests.rs#L387-L416).
- [Runtime confirmation binding, `runtime.rs` lines 357–375](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-sandbox-backend/src/runtime.rs#L357-L375).
- [Delegated test permitting null `backend_audit`, lines 81–107](https://github.com/NVIDIA/OpenShell/blob/b58e24c9dabd6d4bcf2b7186592d3ad50646541b/crates/openshell-sandbox-backend/src/runtime/tests/delegated.rs#L81-L107).

**Interpretation:** source shows trusted backend selection and context binding. It does not independently prove that an admitted delegated backend truthfully enforces the boundary it claims. That is an operator/deployment trust question to verify, not a confirmed vulnerability.

## EABC mapping (candidate criteria, not conformance results)

- `NON_BYPASSABILITY(B,E)`: every path to the protected effect must traverse the declared enforcement boundary.
- `INTEGRITY_DEF(B)`: the declared boundary must be complete and stable.
- `INTEGRITY_STATE(B,E)`: policy/generation changes and revocation must be reflected in enforcement state.
- `INTEGRITY_CTX(C,B,E)`: identity, generation, endpoint/credential context and actual enforcement instance must correspond.
- EBP assurance constraints such as enforcement independence and temporal consistency remain separate from the EABC semantic properties.

## Outstanding verification

Run the matrix against this exact commit and record host, driver, configuration/policy hashes, commands, timestamps, upstream canary records, and artifacts. Until then, all runtime outcomes remain **NOT TESTED**.
