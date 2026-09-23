# 015 — T11 Audit-Chain Request Binding

## Source baseline

cMCP commit `f8743e013786b094caaa70c336519834e73c74d5`.

The audit chain contains a `request_payload_hash` field described by the implementation as a SHA-256 hash of the canonical request payload, without retaining the payload itself. The proxy computes this hash from the JSON-serialized **tool arguments**:

`json.dumps(arguments, sort_keys=True, separators=(",", ":"))`

and stores the resulting SHA-256 value in the final audit entry.

The execution-correlation test also verifies that this hash is present on the refusal record when a valid `execution_id` cannot be operationally correlated.

## Important correction to T10

T10 correctly found that the public GatewayClaim transcript omits raw parameters and does not expose a per-call request digest.

T11 now establishes that the **internal hash-chained AuditEntry does contain a request hash**.

However, the implementation shows that this hash is calculated from the tool `arguments`, not from the complete MCP wire request.

Therefore:

- privacy-preserving argument binding: DEMONSTRATED;
- exact argument identity in the audit chain: DEMONSTRATED;
- complete wire-request identity: NOT DEMONSTRATED;
- commit identity binding: NOT DEMONSTRATED;
- external effect binding: NOT DEMONSTRATED.

## T11 classification

| Evidence property | Result |
|---|---|
| AuditEntry has request hash | DEMONSTRATED |
| Hash is SHA-256 | DEMONSTRATED |
| Raw arguments omitted from audit entry | DEMONSTRATED |
| Hash is deterministic over canonical arguments | DEMONSTRATED |
| Tool identity separately recorded | DEMONSTRATED |
| Execution ID separately recorded | DEMONSTRATED |
| Exact tool arguments can be bound to audit entry | DEMONSTRATED |
| Full MCP JSON-RPC request bound | NOT DEMONSTRATED |
| Policy decision cryptographically bound to same commit object | NOT DEMONSTRATED |
| request hash + execution_id + commit event form a commit object | NOT DEMONSTRATED |
| External effect bound to same digest | NOT DEMONSTRATED |

## EABC consequence

This is a stronger result than T10 alone.

cMCP already has the ingredients for a privacy-preserving request-evidence relation:

`tool_name + request_payload_hash + execution_id + policy_decision + hash-chain position`

But those fields remain **audit facts**, not a demonstrated EABC commit object.

The remaining interoperability gap is therefore increasingly precise:

`Audit evidence ≠ execution commit`

unless the runtime establishes an enforceable relationship between the evidence fields and the exact forwarding event.

## Next

T12 should inspect the exact point where `request_payload_hash` is created relative to:

1. Cedar evaluation;
2. DLP / response inspection;
3. upstream forwarding;
4. audit-entry creation.

The question is whether the hash is merely recorded after the decision or is already the exact immutable value carried through the forwarding path.
