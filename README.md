# EABC × AgenTrust Interoperability

Experimental interoperability and reducibility testing between the EABC execution-boundary contract and open AgenTrust components.

## Purpose

This repository tests, rather than assumes, whether AgenTrust components—starting with cMCP—can instantiate or interoperate with the EABC execution-boundary contract.

The first target is:

> **Can AgenTrust cMCP be used as an EABC execution-boundary implementation for the MCP tool-call domain, and what additional contract is required to bind authorization to the exact committed effect?**

This is an independent technical experiment. It is not a claim that AgenTrust implements EABC, nor an audit or security certification of AgenTrust.

## Method

We distinguish:

- **Documented** — stated by the upstream project.
- **Implemented** — present in the inspected source at a pinned commit.
- **Observable** — visible through a stable runtime/test interface.
- **Demonstrated** — reproduced by an experiment in this repository.

EABC mapping uses the normalized structure:

**Property → Mapping → Assumptions → Gap → Evidence**

No result is assigned in advance.

## Initial target

- Upstream: agentrust-io/cmcp
- Initial release: v0.5.0
- Execution domain: MCP tool calls
- First environment: software-only developer mode
- Later phase: hardware-backed TEE / attestation where infrastructure permits

cMCP documents software-only developer mode for machines without TPM/TEE and states that enforcing mode blocks denied calls before forwarding. The upstream project also states that the upstream MCP tool server remains outside the TEE. These are inputs to the experiment, not conclusions about EABC equivalence.

## Initial EABC stages

The test model follows the EABC interoperability contract:

Governance / Decision Domain → AO → AEE → ECT → PREPARE → FINAL_AUTHORITY_CHECK → COMMIT GATE → EAtt → Execution Domain → EFFECT

The experiment will test how cMCP's actual runtime stages map onto these stages.

## Non-goals

- proving physical or hardware isolation on a software-only runner
- declaring cMCP secure or insecure
- replacing AgenTrust's own tests
- treating attestation, authorization, execution evidence, and transparency as the same property
- assuming that a signed claim proves the physical effect occurred

## Evidence discipline

Every substantive result should identify:

- upstream repository and exact commit/tag
- experiment repository and exact commit
- test vector
- observed result
- evidence artifact and hash where applicable

ABSENT and GAP are kept distinct.

## Current execution-boundary status

The current experimental sequence has established:

- **T31 — Common seam:** the inspected pinned cMCP runtime has one identified common production forwarding transition for the declared HTTP and stdio tool-call consequences.
- **T32 — Exclusivity:** a disposable runtime experiment demonstrates that EABC admission can gate that forwarding transition under two explicit profiles: OPTIONAL (legacy non-correlated calls remain allowed) and MANDATORY (every tool call requires EABC admission).
- **T33 — Native integration contract:** a proposed transport-independent contract now defines the minimum semantics required for a future native cMCP/AgenTrust ↔ EABC integration.

T33 is a **proposed contract, not native cMCP conformance**. It does not claim that upstream cMCP currently requires or implements EABC.

See: `docs/058-t32-execution-boundary-exclusivity.md` and `docs/059-t33-native-integration-contract.md`.

## Status

**Experimental execution-boundary phase — T31/T32/T33.**

T31/T32 provide experimental seam and exclusivity evidence against pinned cMCP source. T33 records the proposed native integration contract. Native cMCP conformance remains **NOT_CLAIMED**.
