# OpenShell targeted regression evidence — Run 12

## Status

**Targeted regression result: PASS (3/3 named tests).**  
**EABC/SLC conformance conclusion: INCONCLUSIVE.**

This record captures the GitHub Actions result for the named source-level regression tests. It does not claim complete mediation, runtime non-bypassability, or EABC/SLC conformance.

## Provenance

- Audit repository: `omwei-org/eabc-agentrust-interoperability`
- Audit branch: `audit/openshell-sentry-2026-10`
- Audit commit used by successful run: `a530a10bcef6b0c2f588990a0dce56b62008be19`
- Target repository: `NVIDIA/OpenShell`
- Exact target commit: `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`
- Workflow: [OpenShell targeted regression tests](../.github/workflows/openshell-targeted-tests.yml)
- Successful run: [GitHub Actions Run #12](https://github.com/omwei-org/eabc-agentrust-interoperability/actions/runs/39060031418)
- Artifact: `openshell-targeted-regressions-39060031418-1`
- Artifact SHA-256: `6a5d20928e9cff2a7e4e963df3797538e6b2ac8705cef20b193db531839a2fa8`
- Artifact expiry reported by GitHub: 2026-11-16T20:00:24Z

## Per-test results

The successful job completed the source checkout and SHA verification, Rust/tooling setup, named-test listing and execution, and evidence artifact upload. For each test, the workflow required a successful nextest exit code, a JUnit report containing exactly one testcase matching the requested name, and no JUnit failure/error or skip.

| Named test | Result |
| --- | --- |
| `stale_generation_fails_before_relay_context_is_created` | PASS |
| `test_forward_relay_guard_blocks_stale_generation_before_upstream_write` | PASS |
| `credential_guard_does_not_shadow_inspected_endpoint_config` | PASS |

The successful job's step list reports all steps completed with conclusion `success`, including “List and run each named regression test” and “Upload logs, metadata, test listings and JUnit results”.

## Failed prior attempt, retained for auditability

[Run #11](https://github.com/omwei-org/eabc-agentrust-interoperability/actions/runs/39059722272) used audit commit `1e6f820c8802393efd971c7f49d8352160c16876`, before the regex filter correction. It is classified as a **harness failure / invalid test attempt**, not a test failure. Its result must not be combined with Run #12 as a negative test finding.

## Scope and limitations

These are targeted source-level regression tests at the pinned OpenShell commit. They provide evidence only for the three named cases under the tested build/configuration.

They do **not** independently establish:
- that every possible path to a protected upstream action is mediated;
- that the guard cannot be bypassed through an alternate path or separate commit authority;
- end-to-end runtime behavior against a canary upstream or equivalent external side-effect oracle;
- EABC property `NON_BYPASSABILITY`, any EBP conformance outcome, or SLC conformance.

Accordingly, the evidence status for these three targeted tests is **PASS**, while the broader EABC/OpenShell enforcement assessment remains **INCONCLUSIVE** pending a separately designed runtime/alternate-path test.

## Next experiment

Design a bounded runtime test with an observable upstream side effect and explicit control cases:
1. stale generation is rejected and the upstream side-effect counter remains unchanged;
2. current/valid generation is accepted and produces the expected side effect;
3. attempt the same protected action through each identified alternate path, recording whether it reaches the upstream;
4. pin the tested OpenShell SHA, configuration, test harness, and artifact digest.

Do not change broader `GEN-01`–`GEN-04`, `REV-01S`, or `CTL-*` findings based only on this targeted test result.
