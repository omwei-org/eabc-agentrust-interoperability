# EABC / AgenTrust Analysis — Current Conclusion and SLC Rationale

## Purpose

This document records the current conclusion after the detailed analysis and interoperability work against AgenTrust/cMCP, together with the resulting reason for continuing the SLC work.

## What the AgenTrust/cMCP analysis established

The tested cMCP v0.5.0 implementation provides substantial authorization, policy enforcement, attestation, audit, and MCP forwarding mediation capabilities.

The EABC interoperability work demonstrated that selected EABC semantics can be imposed at a real cMCP forwarding seam through an adapter, including:

- exact execution binding;
- explicit EABC COMMIT identity;
- substitution rejection;
- replay rejection;
- COMMIT-to-terminal-audit binding.

This demonstrates interoperability at the tested software seam. It does not establish native EABC conformance of unmodified cMCP.

The important architectural boundary is that cMCP mediates the MCP forwarding paths within its declared application/network topology. Gateway mediation alone does not establish that every possible path to a protected effect must pass through that gateway.

This is not treated as a cMCP implementation defect. It is a consequence of the boundary at which an application gateway operates.

AgenTrust discussion also contains a related distinction in issue #554: deny-based Cedar enforcement at a gateway chokepoint is different from authority that the principal never possessed.

## What we cannot currently claim

The analysis does **not** establish a proven unique capability of EABC over AgenTrust/cMCP in universal effect-path mediation.

The reason is important: the SLC/EABC side has not yet empirically demonstrated the corresponding hardware property either.

The Factory EA MVP currently has:

- L1–L3 software/reference enforcement tested;
- 147/147 tests passing;
- an explicit L4 hardware execution-boundary architecture;
- defined T8 and T10 physical acceptance tests.

But L4 remains architecture/prototype until the physical hardware boundary is implemented and tested.

The repository explicitly states that the current software implementation cannot prevent a sufficiently privileged host from bypassing the process or directly addressing an actuator. T8 is therefore the decisive physical test.

## Current evidence-level conclusion

Therefore:

> **EABC/SLC and cMCP are currently at the same evidence level for universal effect-path mediation: NOT_CLAIMED / OPEN.**

The difference is architectural and developmental:

> **EABC/SLC explicitly defines an execution-boundary model extending toward the protected effect domain and has a concrete L4 path to physical validation. cMCP is an application/network-layer gateway whose mediation is bounded by its declared topology.**

We should not claim that EABC/SLC has already solved hardware enforcement or universal mediation.

## Why SLC still makes sense

SLC addresses a different question from an application gateway:

> Not only “is this request authorized?” but “can the protected effect occur other than through the execution boundary?”

The SLC direction moves the execution boundary toward the effect domain, where the property **Exclusive Physical Path** can become a physically testable claim.

Current state:

| Layer | Status | Meaning |
|---|---|---|
| L1–L3 | Tested | Working software execution boundary properties |
| Routes(x) | Open | Effect paths still need to be closed/verified |
| L4 | Architecture/prototype | Hardware execution boundary not yet proven |
| T8 | Open | Direct host-to-effect bypass requires physical demonstration |
| T10 | Open | Alternate effect interface requires physical demonstration |
| Semantic correctness of Atom | Separate | Independent problem |

The next step is therefore not another software adversarial-test cycle.

The Factory EA MVP repository explicitly identifies the next implementation step as:

> **Select the smallest MCU/controller that gives a clean host ↔ controller ↔ GPIO separation.**

The MCU/controller must support a trust boundary in which:

- the compromised host is an untrusted requester;
- protected governance state is outside host control;
- trusted EA public key material is protected;
- replay state is protected within the stated persistence boundary;
- the controller verifies authorization and payload binding;
- the protected controller owns the sole physical effect GPIO;
- the host has no alternate electrical/software-controlled path to that effect.

The EA private key may be held by a separate trusted signer. If authority origin and effect enforcement are co-located in one MCU, the firmware must prevent the compromised host from turning the MCU into an unrestricted signing oracle.

## Strategic conclusion

SLC is not justified by a claim that L4 is already proven.

It is justified because it provides a concrete, testable path from:

authorization → execution authority → commit → physical effect

to a stronger boundary question:

> **Does the host have any technical capability to cause the protected effect without passing the execution boundary?**

L1–L3 are already tested. L4 is the remaining physical engineering step needed to turn that question into empirical evidence.

## References

- AgenTrust / cMCP: https://github.com/agentrust-io/cmcp
- EABC ↔ AgenTrust interoperability repository: https://github.com/omwei-org/eabc-agentrust-interoperability
- Factory EA MVP: https://github.com/omwei-org/factory-ea-mvp
- L4 hardware requirements: https://github.com/omwei-org/factory-ea-mvp/blob/main/L4_HARDWARE_ENFORCEMENT.md
