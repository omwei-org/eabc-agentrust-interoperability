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

## Status

**Phase 0 — repository and CI baseline.**

The first CI job will pin cMCP v0.5.0, run the upstream unit-test baseline, and record the environment and result before EABC-specific tests are introduced.
