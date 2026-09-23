# 017 — T13 Argument-to-Forwarding Binding and Collaboration Surface

## Source baseline

cMCP commit `f8743e013786b094caaa70c336519834e73c74d5`.

The audited implementation computes `request_payload_hash` from the `arguments` object before policy evaluation. The same Python `arguments` object is subsequently passed through the native ingress gateway and directly into `_forward_to_upstream(call_id, entry, tool_name, arguments, ...)`.

This establishes a strong **same-object execution path** in the current implementation.

## T13 result

The source does not show a second independent serialization/hash comparison immediately before transport. Therefore we can establish:

- the hash is computed before authorization and forwarding;
- the forwarding function receives the arguments object used by the call path;
- the audit entry records the earlier hash;
- there is no demonstrated commit gate that re-verifies the hash against the final serialized wire request.

The strongest defensible classification is:

**ARGUMENT IDENTITY: DEMONSTRATED**  
**WIRE-REQUEST IDENTITY: NOT DEMONSTRATED**  
**COMMIT-TIME RE-VERIFICATION: NOT DEMONSTRATED**

This is not a mutation vulnerability finding. It is a boundary-definition finding.

## Collaboration surface

This creates a concrete, non-competitive EABC × AgenTrust integration point.

cMCP already supplies:

1. Cedar authorization;
2. TEE/hardware-rooted enforcement context;
3. runtime policy binding;
4. execution correlation;
5. privacy-preserving request hashing;
6. hash-chained signed evidence.

EABC can contribute a narrowly defined **commit contract** above the existing cMCP forwarding gate:

`prepare → final authority check → commit(request_digest, execution_id, policy_identity) → effect`

The integration experiment should not replace Cedar, cMCP or TRACE. It should bind their existing outputs at one explicit commit point.

## Proposed interoperability profile

For an MCP-specific EABC profile, define an opaque commit envelope:

- `commit_id`
- `execution_id`
- `request_payload_hash`
- `policy_bundle_hash`
- `authority_epoch` or equivalent version
- `tool_name`
- `effect_target_id`

The exact field semantics should be negotiated with AgenTrust rather than imposed by EABC.

The key invariant is:

`request_payload_hash(EABC commit) == request_payload_hash(cMCP audit)`

and the evidence chain becomes:

`Cedar decision → EABC commit → cMCP forwarding → GatewayClaim/TRACE`

## Why this is a collaboration opportunity

The experiment is no longer looking for a missing security feature in cMCP. It identifies a compositional boundary where both systems already have strong pieces:

- AgenTrust: identity, policy, TEE enforcement, runtime evidence;
- EABC: explicit decision-to-effect commit semantics.

The proposed collaboration can therefore be framed as **interoperability and profile definition**, not remediation of an alleged cMCP weakness.

## Next

T14 should implement the proposed commit envelope in the independent harness and then map each field to an existing cMCP artifact. The implementation should remain outside cMCP initially, so the result shows the minimum additional contract required for interoperability.
