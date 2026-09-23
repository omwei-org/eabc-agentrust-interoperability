# 021 — T17 Cross-Artifact Interoperability Test

## Result

T17 validates the proposed profile against representative cMCP-shaped artifacts.

The test does not yet execute the cMCP runtime. It verifies the cross-artifact contract using the same artifact fields identified in the source audit.

## Verified relations

`AuditEntry.request_payload_hash == EABC.commit.request_payload_hash`

`AuditEntry.execution_id == EABC.commit.execution_id`

`GatewayClaim.policy_bundle_hash == EABC.commit.policy_bundle_hash`

`GatewayClaim.audit_chain_tip == EABC.commit.evidence_ref`

Tampering with arguments produces a digest mismatch. A policy identity mismatch prevents commit construction.

## Interpretation

The experiment demonstrates that the proposed EABC profile can be layered over the existing cMCP evidence vocabulary without duplicating the evidence record.

It does **not** yet demonstrate enforcement at the real cMCP forwarding seam.

## Collaboration artifact

The useful deliverable is now a narrow proposal:

**EABC Execution Commit Profile for MCP**

AgenTrust/cMCP supplies authorization, execution correlation, TEE context and signed evidence. The EABC profile supplies explicit commit semantics and cross-artifact invariants.

## Next phase

The next experiment should move from fixture-level interoperability to a real cMCP integration seam. The adapter should consume an actual cMCP AuditEntry and create the commit before forwarding, then make forwarding contingent on commit verification.

Success criteria:

1. no commit → no forward;
2. request digest mismatch → no forward;
3. policy identity mismatch → no forward;
4. execution identity mismatch → no forward;
5. successful commit → exact arguments forwarded;
6. commit reference appears in terminal evidence.

This is the point at which the collaboration hypothesis becomes an executable integration experiment rather than a document mapping.
