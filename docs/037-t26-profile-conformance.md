# T26 — Profile Conformance Model

A profile implementation is conformant only if each MUST requirement has executable evidence.

| Requirement | Test evidence |
|---|---|
| MCP-EABC-001 exact request binding | T25.6 |
| MCP-EABC-002 commit gate | T25.2 / T25.4 |
| MCP-EABC-003 single-use commit | T25.5 |
| MCP-EABC-004 failure-state preservation | T25.4 |
| MCP-EABC-005 durable binding evidence | T25.7 |
| MCP-EABC-006 native/adapter declaration | T25.8 |
| MCP-EABC-007 scoped mediation | T25.9 |
| MCP-EABC-008 evidence ≠ physical truth | T25.9 |

## Conformance rule

A profile MUST NOT claim conformance when a MUST requirement is only described but lacks executable evidence.

A profile MAY claim partial conformance when all demonstrated requirements are explicitly scoped and remaining requirements are marked unproven.

## Current experimental status

The T25/T26 evidence set demonstrates all listed MUST invariants at the EABC interoperability adapter.

The reusable `eabc_profile` adapter is implemented and its conformance tests pass.

The validated upstream is cMCP v0.5.0 at source revision `d03b9af504535d3d43f192bc6d9eff89b8afd12f`.

The final evidence set is bound by the CI-generated T26.7 manifest to repository revision `c7a53b1c148fa6080dd5c8553388bf560dbb5873`.

This does not establish native conformance of unmodified cMCP v0.5.0.

**Result: EXPERIMENTAL_PASS.**

**Native cMCP conformance: NOT_CLAIMED.**