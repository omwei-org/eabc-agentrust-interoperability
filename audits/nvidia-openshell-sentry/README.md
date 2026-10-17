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
- [OpenShell pinned-source evidence](evidence/openshell-a4c848a.md)

## Initial baseline

OpenShell source review is pinned to [`a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`](https://github.com/NVIDIA/OpenShell/commit/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317). The review environment could not resolve GitHub/raw GitHub hosts for local checkout/runtime testing. Source/documentation inspection was performed through repository connector access; no runtime tests were executed. Therefore, runtime status remains NOT TESTED unless a later dated execution record is added.

## Working rule

Every finding must state: claim, EABC relevance, evidence and pinned reference, counter-evidence/limits, status, and next falsification test. Keep vendor-specific features distinct from EABC conformance claims.