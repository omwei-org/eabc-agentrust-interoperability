# 008 — T04 Action Binding Audit

## Source baseline

Audited against cMCP commit `f8743e013786b094caaa70c336519834e73c74d5`.

The upstream cMCP specification contains an **Execution Action Binding v1** proposal and a **Session Independent Execution Correlation** design.

The action binding is defined as a JCS/RFC 8785 digest over exactly six fields:

- domain
- version
- agent_id
- action_type
- action_scope
- action_timestamp

The binding is intended to distinguish a logical executable operation. A different binding under the same authenticated-agent + execution_id reservation is specified as a conflicting/mutated operation and must be refused before upstream invocation.

## Critical implementation boundary

The same upstream documents explicitly state that the execution registry/action-binding integration is **not operational in the current gateway**.

A valid supplied `execution_id` is currently refused with `execution_correlation_unavailable` before upstream invocation. The standalone registry is a non-operational foundation.

Therefore we must distinguish the contract from runtime enforcement.

## EABC mapping

| EABC property | cMCP evidence | Result |
|---|---|---|
| Logical execution identity | `execution_id` | DEMONSTRATED as a designed/validated correlation field |
| Exact action binding | Execution Action Binding v1 | SPECIFIED |
| Canonical binding | RFC 8785/JCS + SHA-256/SHA-384 | SPECIFIED |
| Mutation detection | Different binding must be refused | SPECIFIED, runtime integration pending |
| No forward on unavailable correlation | Current gateway refusal path | DEMONSTRATED |
| Binding active at commit | Integrated runtime registry | NOT DEMONSTRATED |
| Binding atomically reserved before invocation | Required by design | NOT DEMONSTRATED |
| Binding survives crash/recovery | Required by design | NOT DEMONSTRATED |
| Exact request == committed action | Not established by current contract alone | NOT DEMONSTRATED |
| External effect == committed action | Explicitly outside the binding contract | NOT DEMONSTRATED |

## Key conclusion

This is stronger than a simple correlation identifier: cMCP has a defined direction toward **logical-operation binding**.

But the current v0.5.0 gateway does not provide that as an active execution commitment. The execution-correlation/action-binding work is a designed future enforcement foundation, with explicit admission, terminal-state, durability, recovery and replay requirements still pending.

Accordingly, this experiment must not classify `execution_id` as an EABC `commit_id`.

The correct current distinction is:

`execution_id` = validated correlation / future logical-operation binding

versus

`EABC commit_id` = authoritative commit event binding exact execution request to effect.

## Why this matters

The upstream design itself separates:

`attempt identity != logical operation identity != external outcome identity`

That separation is directly compatible with the EABC/AAC distinction:

`MAY → COMMIT → DID`

The remaining interoperability question is whether the eventual cMCP integration can make the logical action binding part of an enforceable commit path, rather than merely an evidence/correlation mechanism.
