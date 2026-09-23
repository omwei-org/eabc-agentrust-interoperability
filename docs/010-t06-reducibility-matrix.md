# 010 — T06 cMCP → EABC Reducibility Matrix

Source baseline: cMCP repository and its current published architecture. The upstream README states that every tool call is intercepted, evaluated by Cedar, enforced in the TEE, and recorded in the audit chain; it also states that the signed TRACE claim records the policy decision and audit chain. citeturn0view1

| T05 / EABC invariant | cMCP mechanism | Classification | Evidence boundary |
|---|---|---|---|
| PREPARE exact request | incoming MCP tool call + request construction | PARTIAL | request exists, but no EABC prepare object |
| request digest | canonical request/action binding concepts | PARTIAL / SPECIFIED | exact commit binding not demonstrated |
| FINAL_AUTHORITY_CHECK | Cedar allow/deny + enforcement path | PARTIAL | policy decision is real; EABC final-authority semantics not established |
| authority epoch | execution correlation/action-binding design | NOT DEMONSTRATED | no demonstrated atomic authority snapshot |
| COMMIT | enforcing allow → forwarding gate | SCOPED | strong forwarding control, but not universal effect commit |
| commit_id | execution_id | NOT EQUIVALENT | execution identity/correlation is not automatically a commit event |
| committed request digest | action binding | SPECIFIED / NOT ACTIVE | logical action binding exists as design; runtime commit binding not demonstrated |
| EFFECT binding | upstream forwarding | DEMONSTRATED at transport seam | exact received MCP request observed in T03 |
| failure: no authority/correlation | fail closed / no forward | DEMONSTRATED | refusal path prevents upstream invocation |
| evidence | GatewayClaim / audit chain | STRONG | signed claim and chain are evidence artifacts |
| physical effect binding | downstream tool/physical system | NOT DEMONSTRATED | outside current cMCP boundary |

## Result

cMCP is **substantially reducible to an EABC execution-boundary instance for the MCP tool-call domain**, but the reduction is not complete.

The strongest correspondence is:

`Cedar decision → enforcing forwarding gate → upstream MCP request`

The unresolved EABC additions are specifically:

1. an explicit commit object;
2. atomic binding of authority snapshot + exact request;
3. commit-time state/epoch semantics;
4. independently enforceable binding of the committed request to the eventual external effect.

This is a narrower statement than “cMCP implements EABC” and a stronger statement than “cMCP is unrelated to EABC.”

## Important source distinction

cMCP's own architecture already provides a genuine enforcement boundary: the gateway intercepts calls and enforcing mode prevents denied calls from being forwarded. citeturn0view1

Therefore the remaining EABC question is not whether cMCP has a boundary at all. It is whether that boundary has the complete **authority → exact-request → commit → effect** semantics defined by EABC.
