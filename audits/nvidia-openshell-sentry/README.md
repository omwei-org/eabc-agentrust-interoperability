# NVIDIA OpenShell / Sentry — EABC audit

## Purpose

Track an evidence-based review of NVIDIA OpenShell and NVIDIA Sentry against the EABC execution-boundary model. This audit is separate from the repository's AgenTrust/cMCP interoperability experiment; it does not change that experiment's scope or conclusions.

## Scope

1. OpenShell standalone.
2. Sentry standalone.
3. OpenShell + Sentry composition, where supported and evidenced.
4. EABC-relevant properties: non-bypassability, boundary integrity, integrity of state/context, and exclusivity; record enforcement-substrate assumptions separately as EBP assurance constraints.

## Evidence discipline

Use the following status labels consistently:

- **DOC-CLAIM**: a vendor/upstream documentation statement; not independently verified by runtime testing.
- **SOURCE**: behavior or control observed in pinned implementation source.
- **TEST-CONTRACT**: a test exists and asserts the stated behavior; this does not mean it was run.
- **RUNTIME**: evidence from an executed test in a recorded environment with commands, versions, observed results and artifacts.
- **NOT ASSESSED**: evidence has not yet been collected to evaluate the claim.

Keep evidence class separate from test result. Runtime result vocabulary: **NOT TESTED**, **INCONCLUSIVE**, **PASS**, **FAIL**. Use **NOT REPRODUCED** only after an actual reproduction attempt was executed and its conditions/results recorded.

Do not convert a source-level test into a claim of runtime validation. Do not report a vulnerability solely because a control was not found in the files reviewed. Record pinned commits and platform/driver scope for every conclusion. Every finding must include its evidence class, an explicit EABC criterion mapping (or state that mapping is not yet assessed), and permalink(s) to the pinned source/documentation with line ranges wherever available. A candidate EABC mapping is not a conformance result.

## Current documents

- [Findings register](findings.md)
- [Runtime test matrix](test-matrix.md)
- [OpenShell pinned-source evidence — original baseline `a4c848a`](evidence/openshell-a4c848a.md)
- [OpenShell follow-up source review — newer commit `b58e24c`](evidence/openshell-b58e24c.md)

## Initial baseline

OpenShell source review is pinned to [`a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`](https://github.com/NVIDIA/OpenShell/commit/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317). The review environment could not resolve GitHub/raw GitHub hosts for local checkout/runtime testing. Source/documentation inspection was performed through repository connector access; no runtime tests were executed. Therefore, runtime status remains NOT TESTED unless a later dated execution record is added.

## Upstream drift — separate review required

The initial findings and original matrix remain scoped to `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`. A later comparison checked upstream commit `b58e24c9dabd6d4bcf2b7186592d3ad50646541b` (13 commits ahead at the time of comparison). That range materially changed the isolation interface, provisioning-evidence contract, RPC runtime and conformance tests. See [BASELINE-01 and BASELINE-02 in the findings register](findings.md) and the [baseline-drift gate and added tests](test-matrix.md).

The source review found that the older common contract explicitly required four outer-fence guarantees, while the newer common contract binds native evidence to a generation and explicitly warns that the digest is not independent proof of enforcement. This is an **assurance-contract difference, not a confirmed vulnerability**. Partial counter-evidence has now been inspected: Docker and Podman verify actual container network configuration, while the VM source uses QEMU `-nic none` and configures libkrun with vsock/virtiofs rather than an IP NIC. These source-level controls reduce the basis for a claim of a direct-egress defect, but they do not replace runtime evidence or settle revocation/controller-loss behavior, all platform variants, or delegated-backend assurance.

Do not silently replace the original pinned baseline. For any new runtime result, state the exact commit, driver, environment and evidence artifacts. A newer-upstream review should use a distinct execution record and revise scope only after examining the new validation paths.

## Follow-up source review

A targeted follow-up review was recorded for OpenShell commit `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`. It adds source counter-evidence for generation guards, credential guard behavior, driver-level isolation checks and delegated-backend admission. It is **not** a complete re-audit of the newer commit, and no runtime tests were executed. The original findings and runtime matrix remain pinned to `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`; do not transfer findings or test results across commits without a commit-specific review and execution record.

The current policy schema documents `allow_uninspected_credentials` as a security-sensitive explicit opt-in for credentialed traffic that cannot be inspected. See [NVIDIA policy schema](https://docs.nvidia.com/openshell/latest/reference/policy-schema). Documentation is `DOC-CLAIM`, not runtime evidence.

## Working rule

Every finding must state: claim, EABC relevance, evidence and pinned reference, counter-evidence/limits, status, and next falsification test. Keep vendor-specific features distinct from EABC conformance claims.