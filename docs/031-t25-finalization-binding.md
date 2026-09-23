# T25.3 — EABC Commit ↔ cMCP Finalization Binding

## Question

Can cMCP's existing `_CallFinalizationState` carry the binding between an EABC COMMIT and the specific execution attempt without inventing a new execution identifier?

## Method

The experiment uses the real `CMCPProxy.call_tool()` implementation and the existing `_forward_to_upstream(..., finalization=...)` seam.

Binding tested:

EABC `commit_id`
→ cMCP `call_id`
→ `_CallFinalizationState`
→ `request_payload_hash`
→ forwarding
→ terminal audit persistence

No production cMCP source is modified.

## Result

**PARTIAL / ADAPTER-DEMONSTRATED**

The existing finalization object is passed through the real call path and is available at the forwarding seam. The experiment can bind an EABC `commit_id` to that same object while preserving the cMCP `call_id` and request digest.

However, `_CallFinalizationState` currently has no normative EABC commit field, and the production terminal audit serialization does not persist `eabc_commit_id`.

Therefore this does **not** demonstrate native EABC evidence binding in unmodified cMCP.

## What is demonstrated

- real `CMCPProxy.call_tool()` creates and carries finalization state;
- the forwarding seam receives that same finalization object;
- EABC commit identity can be bound to the execution attempt at the seam;
- request digest remains available for exact-request correlation;
- commit enforcement can fail closed before forwarding.

## Remaining gap

To make the binding native rather than adapter-level, cMCP would need an explicit contract for carrying the EABC commit identity into terminal evidence, with defined integrity and lifecycle semantics.

The experiment intentionally does not implement that change.

## Evidence

Test: `tests/test_t25_finalization_binding.py`

Commit: `25e29a976b16bbc3440fdf85eab2df6d194548d5`

Status: **READY FOR CI VALIDATION**
