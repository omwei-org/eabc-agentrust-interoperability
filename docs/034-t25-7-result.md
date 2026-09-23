# T25.7 — Durable Evidence Binding Result

## Status

**PASS**

Experiment revision: `0bf878c5108ce05c3cd2b6d0ea0a2b4f946750b5`  
CI run: `35862127681`  
Upstream: public cMCP `v0.5.0`

## Question

Can the interoperability layer construct a deterministic evidence object that binds the EABC COMMIT to the exact cMCP execution tuple and terminal audit record?

## Result

PASS.

The binding object contains:

- `commit_id`
- `call_id`
- `tool_name`
- `request_payload_hash`
- `policy_id`
- `terminal_audit_hash`

The canonical representation is deterministically hashed. Mutation of any individual binding field changes the evidence hash.

## Interpretation

This establishes a durable, content-addressed representation of the cross-layer binding:

`EABC COMMIT → exact cMCP execution tuple → terminal audit`

This is stronger than merely storing an audit record because the binding explicitly includes the EABC commit identity.

## Important scope distinction

The evidence object is produced by the **EABC interoperability layer**. It is not a new native cMCP AuditEntry field.

Therefore T25.7 demonstrates that the missing cross-layer relation can be represented deterministically, but does not claim that unmodified cMCP v0.5.0 natively produces EABC commit binding evidence.

## Conclusion

**T25.7 PASS.**

The interoperability layer can produce deterministic durable evidence binding an EABC COMMIT to the exact cMCP execution tuple and terminal audit hash.
