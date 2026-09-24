# T30.3 — Actual cMCP runtime patch experiment

## Purpose

T30.3 is the first experiment that places an EABC admission hook at the actual cMCP runtime forwarding transition.

It MUST NOT be interpreted as evidence that cMCP itself is an EABC execution boundary. The experiment explicitly separates native cMCP behavior from the EABC-added hook.

## Evidence-tier separation

### Native cMCP stages

At the pinned upstream revision, these stages belong to cMCP:

- authenticated request handling;
- request serialization / request payload hashing;
- execution-correlation handling;
- Cedar authorization;
- catalog / upstream resolution;
- the existing forwarding operation;
- audit / TRACE evidence.

### Added by this experiment

The following are experimental additions made by this repository:

- EABC FINAL_AUTHORITY_CHECK;
- EABC COMMIT validation;
- EABC execution/action binding admission;
- commit single-use / terminal-state guard where exercised;
- the experimental handoff condition immediately before upstream forwarding.

Therefore: **cMCP + EABC hook** may demonstrate an EABC-controlled forwarding transition; it does not demonstrate that cMCP alone implements EABC.

The result must remain classified as **Demonstrated: experimental integration**, not **Implemented: native cMCP EABC support**.

## Pin discipline

T30.3 uses two explicitly different references when necessary:

1. **Released baseline:** cMCP v0.5.0 at `d03b9af504535d3d43f192bc6d9eff89b8afd12f`, confirmed by the published 0.5.0 release provenance.
2. **Execution-correlation experiment:** cMCP `f8743e013786b094caaa70c336519834e73c74d5`, a later revision that MUST NOT be described as the v0.5.0 release unless independently verified to be that exact tag commit.

This distinction preserves comparability with R11-R and T27.

## Runtime experiment

The target path is:

    real CMCPProxy.call_tool()
      -> native cMCP request / identity handling
      -> native execution-correlation handling
      -> native Cedar authorization
      -> EABC FINAL_AUTHORITY_CHECK
      -> EABC COMMIT validation
      -> existing upstream forwarding
      -> real local MCP upstream
      -> observable external consequence

The patch MUST introduce no second forwarding path.

## Observable consequence

The local MCP upstream MUST perform an externally observable operation rather than merely incrementing an in-memory test counter.

Minimum sink:

- append a canonical event record to a dedicated file;
- fsync the file before reporting success;
- calculate and record the SHA-256 digest of the canonical event;
- expose the resulting artifact to the test runner.

The file sink demonstrates an observable software consequence. It does not prove an external physical effect.

## TOCTOU / race experiment

T30.3 MUST include a coordinated race between authority validation and forwarding. One worker pauses after authority validation while another invalidates the authority state; forwarding is then released. The result must distinguish validation once across a mutable interval from a final authority check at the commit transition.

A race result MUST NOT be interpreted as a vulnerability in cMCP unless the tested path is production-reachable and the authority mutation is within the stated threat model.

## Evidence artifacts

Every T30.3 run MUST emit a machine-readable evidence bundle containing the upstream repository, exact upstream commit, release/tag reference when applicable, experiment repository commit, test vector, native cMCP stages, experimental EABC stages, execution_id, call_id, request payload hash, policy/config identity, commit_id when present, terminal state, upstream consequence status, sink artifact path, sink SHA-256, and test result.

CI MUST hash the final bundle and publish the hash in the workflow artifact/output.

## Claim boundaries

T30.3 may demonstrate an experimentally integrated EABC admission condition, exact request/execution binding, observable software consequence after admission, refusal of specified substitutions/replays, and observed behavior under the defined race experiment.

It does NOT demonstrate native EABC support in cMCP, complete mediation of every cMCP ingress, hardware isolation of the EABC hook, exactly-once external-world execution, physical safety, or proof that a real-world physical effect occurred.

## Decisive question

> **For the declared MCP-forwarding consequence, is the experimental EABC admission hook placed at the actual transition through which the selected runtime path produces the consequence, and can any tested production-reachable alternative path produce the same consequence without that hook?**
