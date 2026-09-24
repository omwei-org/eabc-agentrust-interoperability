# EABC × AgenTrust Interoperability

Experimental interoperability and execution-boundary testing between the EABC execution-authority contract and open AgenTrust components.

## Purpose

This repository tests, rather than assumes, whether AgenTrust components—starting with cMCP—can interoperate with the EABC execution-boundary contract.

> **Can an EABC COMMIT become an explicit admission condition for cMCP's existing upstream forwarding transition, while preserving cMCP identity, Cedar authorization, TEE enforcement, audit, and TRACE semantics?**

This is an independent technical experiment. It is not a claim that AgenTrust implements EABC, nor an audit or security certification of AgenTrust.

## Method

We distinguish:

- **Documented** — stated by the upstream project.
- **Implemented** — present in inspected source at a pinned commit.
- **Observable** — visible through a stable runtime/test interface.
- **Demonstrated** — reproduced by an experiment in this repository.

EABC mapping uses: **Property → Mapping → Assumptions → Gap → Evidence**.

## Current target

- Upstream: `agentrust-io/cmcp`
- Original baseline: `v0.5.0`
- Current execution-correlation characterization: `f8743e013786b094caaa70c336519834e73c74d5`
- Execution domain: MCP tool-call forwarding
- Integration mode: software-only experimental harness

The original T27 baseline uses cMCP v0.5.0. Later experiments characterize the execution-correlation revision above. In that revision, a supplied valid `execution_id` is currently handled fail-closed as `execution_correlation_unavailable`; it does not yet activate a native EABC-compatible forwarding admission path.

## Execution-boundary model

```text
authenticated request
  → execution_id + immutable action binding
  → cMCP authorization
  → EABC FINAL_AUTHORITY_CHECK
  → EABC COMMIT
  → existing cMCP upstream forwarding
  → upstream MCP consequence
  → cMCP audit / TRACE
```

The declared consequence for the MCP profile is:

> **the MCP request reaches the configured upstream MCP server.**

EABC contributes execution authority at this declared boundary; cMCP retains its existing identity, policy, attestation, audit, and transparency mechanisms.

## Work completed

### T27 — reproducible EABC–cMCP interoperability

Software-level reproducibility with deterministic vectors, pinned cMCP revision, provenance, and failure semantics. T27 does **not** claim native cMCP EABC conformance, hardware enforcement, physical effect verification, or privileged-bypass resistance.

### T28 — cMCP/EABC property mapping

Mapped cMCP's runtime path and evidence model against EABC properties. The principal unresolved property identified was **exclusive mediation of the declared consequence**.

### T29 — forwarding-boundary experiments

T29 examined whether cMCP's forwarding boundary can serve as the declared execution consequence boundary. Private direct invocation of internal forwarding methods is deliberately not treated as a production bypass.

### T29.3 — execution binding

EABC COMMIT binds authenticated agent identity, `execution_id`, `call_id`, `tool_name`, canonical request payload hash, policy identity, immutable action binding, and authority reference. Substitution and single-use replay cases are tested.

### T29.4 — execution admission

Models reservation → COMMIT validation → forwarding admission and tests missing COMMIT, substituted identity/action, terminal replay, outcome-unknown replay, and reservation conflicts.

### T29.5 — cMCP execution seam characterization

The later cMCP execution-correlation revision was inspected and pinned. Its fail-closed behavior is documented as a current runtime boundary, not as native EABC support.

### T30 — admission seam proposal

Defines the smallest proposed interoperability contract: cMCP identity/execution binding → cMCP Cedar authorization → EABC FINAL_AUTHORITY_CHECK → EABC COMMIT → existing forwarding transition → cMCP audit/TRACE. The proposal explicitly avoids introducing a second forwarding path.

### T30.1 / T30.2 — runtime-shaped harnesses

T30.1 defines the experimental cMCP adapter seam. T30.2 exercises a controlled forwarding transition and observes whether the modeled consequence occurs only after valid EABC admission. These remain harness-level results, not native cMCP conformance.

## Evidence discipline

Every substantive result should identify the upstream repository and exact commit/tag, experiment repository and exact commit, test vector, observed result, and evidence artifact/hash where applicable.

**ABSENT**, **GAP**, **UNPROVEN**, and **DEMONSTRATED** are kept distinct.

## Non-goals

- declaring cMCP secure or insecure
- declaring native EABC support without upstream/runtime evidence
- proving physical or hardware isolation on a software-only runner
- proving exactly-once external execution
- proving that an external physical effect occurred
- replacing AgenTrust's own tests or security model
- treating authorization, attestation, execution authority, execution evidence, and transparency as the same property

## Next decisive experiment

**T30.3 — actual cMCP runtime patch experiment.**

The next step is to apply the smallest experimental hook to the pinned cMCP runtime immediately before its existing upstream forwarding operation:

```text
real CMCPProxy.call_tool()
  → real execution correlation
  → real cMCP authorization
  → EABC admission / COMMIT
  → real upstream forwarding
  → real local MCP upstream
```

The decisive question is:

> **Does every production-reachable path capable of causing the declared MCP-forwarding consequence pass through the same EABC admission boundary?**

A private test call into an internal method is not sufficient evidence of a bypass. Conversely, a production-reachable path that reaches the same upstream consequence without a valid EABC COMMIT would be material evidence against exclusive mediation by the proposed boundary.

## Status

**Phase 3 — execution-admission interoperability experiment.**

The repository has progressed from baseline/property mapping to execution binding, admission semantics, cMCP seam characterization, and a concrete interoperability contract. Native cMCP integration remains an open experiment.
