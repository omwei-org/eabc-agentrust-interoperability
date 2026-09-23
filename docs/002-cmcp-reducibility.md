# 002 — cMCP Reducibility Model

## EABC reference pipeline

Governance / Decision Domain → AO → AEE → ECT → PREPARE → FINAL_AUTHORITY_CHECK → COMMIT GATE → EAtt → Execution Domain → EFFECT

## cMCP candidate pipeline

MCP request → Cedar context → Cedar authorize() → enforcement/DLP → forward upstream → MCP response → TRACE/audit evidence

This is a **candidate mapping**, not a finding.

## Initial mapping questions

| EABC stage | cMCP candidate | Question |
|---|---|---|
| AO | MCP request + authenticated principal | Does the request identify the actor and intended resource sufficiently? |
| AEE | Cedar policy evaluation | Does Cedar evaluation correspond to the EABC authorization-evaluation stage? |
| ECT | Request + policy context | Is the execution context complete and bound to the exact request? |
| PREPARE | Request/context construction | Is there an explicit prepared execution object? |
| FINAL_AUTHORITY_CHECK | Final enforcement decision | Is the last authority decision explicit and final before forwarding? |
| COMMIT GATE | Enforcing-mode allow + forwarding | What exactly becomes committed: permission to forward, or the exact execution object? |
| EAtt | GatewayClaim / audit evidence | Does the evidence bind authority, request, commit and effect as required by EABC? |
| Execution Domain | Upstream MCP server | What is inside and outside the enforcement boundary? |
| EFFECT | Actual MCP tool effect | Can the exact effect be demonstrated and bound to the commit? |

## Important non-equivalences

### Cedar authorization is not automatically EABC FINAL_AUTHORITY_CHECK

Cedar may provide the authorization evaluation stage. Equivalence to the final authority check requires evidence about timing, inputs, policy state, and the decision's relationship to the subsequent effect.

### Forwarding is not automatically EABC COMMIT

A gateway can commit to forwarding a request while the downstream system remains the authority over the eventual effect.

The experiment must therefore answer:

> **What exactly is committed?**

### GatewayClaim is not automatically EABC EAtt

A signed evidence object can prove what a gateway recorded without proving that it contains all bindings required by the EABC execution-attestation contract.

## Result vocabulary

- **FULL** — tested behavior satisfies the defined EABC requirement for the tested scope.
- **PARTIAL** — only a scoped or subset property is demonstrated.
- **ABSENT** — the tested system has no corresponding mechanism for the requirement in scope.
- **NOT DEMONSTRATED** — the mechanism may exist, but this experiment does not establish it.
- **GAP** — a specific additional property is required to reach the EABC contract.

ABSENT is not used merely because an experiment was not run; that case is NOT DEMONSTRATED.
