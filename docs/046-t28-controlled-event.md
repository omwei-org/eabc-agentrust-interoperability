# T28 — Controlled TRACE × EABC Shared Event

T28 closes the cross-source binding gap identified during the IV-002 review.

It defines one deterministic controlled event and records evidence from two independent surfaces against the same event:

- TRACE-side action evidence uses the published TRACE embodied-action receipt shape.
- EABC-side evidence records the execution-boundary commit for the exact execution tuple.
- A third, dependency-free verifier checks the binding without trusting a narrative bridge.

## Controlled event

| Field | Value |
|---|---|
| event_id | `eabc-trace-controlled-001` |
| session_id | `trace-session-t28-001` |
| call_id | `call-t28-001` |
| agent_id | `did:web:agent.example:cell-a:planner-1` |
| action_type | `material.move` |
| action_scope | `cell-a.material.move` |
| action_timestamp | `2026-09-26T06:30:00Z` |
| target | `did:web:factory.example:cell-a:material-station-1` |

The action reference is SHA-256 over canonical JSON containing `agent_id`, `action_type`, `action_scope`, and `action_timestamp`, following the published TRACE action-receipt fixture contract.

## Binding

The same `event_id`, `call_id`, and `action_ref` are present in both evidence surfaces. The EABC evidence additionally binds the event to:

`commit_id → tool_name → request_payload_hash → policy_id → ALLOW → COMMIT → EFFECT`

The exact EABC request contains the TRACE `action_ref`, so a change to the action reference changes the EABC request digest.

## Independent verification

`tests/test_t28_controlled_event.py` recomputes the action reference, EABC request digest, TRACE evidence digest, cross-source binding digest, and terminal result. It also mutates the shared action reference and requires the binding to fail.

## Claim boundary

T28 demonstrates a **reproducible cross-source event binding fixture**. It does not claim that this fixture is a signed TRACE Trust Record, that a physical action occurred, that TRACE independently attested the physical world, or that EABC provides hardware isolation in this experiment.

The purpose is narrower: an independent ingest can see exactly which TRACE action evidence and which EABC commit evidence refer to the same controlled event, and can verify that relationship from bytes.
