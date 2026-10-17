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

- **CONFIRMED — source**: directly supported by pinned source or documentation.
- **CONFIRMED — test contract**: a named test exists and asserts the stated behavior; this does not mean it was run.
- **CONFIRMED — runtime**: reproduced in a recorded environment with commands, versions, output, and artifacts.
- **NOT REPRODUCED**: an attempted reproduction did not demonstrate the issue; include conditions and limitations.
- **NOT TESTED**: no adequate runtime test has been performed.
- **NOT CONFIRMED**: available evidence is insufficient to establish the claim.
- **NOT CLAIMED**: the vendor/source does not appear to make the claim being discussed; do not treat this alone as a defect.

Do not convert a source-level test into a claim of runtime validation. Do not report a vulnerability solely because a control was not found in the files reviewed. Record pinned commits and platform/driver scope for every conclusion.

## Current documents

- [Findings register](findings.md)
- [Runtime test matrix](test-matrix.md)
- [OpenShell pinned-source evidence](evidence/openshell-a4c848a.md)

## Initial baseline

OpenShell source review is pinned to [`a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`](https://github.com/NVIDIA/OpenShell/commit/a4c848adbddd0b4732fd70ddcf8a563a5b1e9317). The review environment could not resolve GitHub/raw GitHub hosts for local checkout/runtime testing. Source inspection was performed through repository connector access; runtime claims therefore remain unverified unless explicitly documented otherwise.

## Working rule

Every finding must state: claim, EABC relevance, evidence and pinned reference, counter-evidence/limits, status, and next falsification test. Keep vendor-specific features distinct from EABC conformance claims.