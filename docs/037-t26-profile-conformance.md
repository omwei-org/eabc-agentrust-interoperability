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

The T25 evidence set demonstrates all listed MUST invariants at the EABC interoperability adapter.

It does not establish native conformance of unmodified cMCP v0.5.0.

The next implementation target is to replace disposable test gates with a reusable profile adapter and run the same conformance suite against it.
