# IV-002 Path-2 — Shared Controlled Event

Path-2 tests whether independently produced EABC and TRACE evidence can be correlated to one execution event without changing either system's semantics.

This is a new controlled event, not a reconstruction of the original IV-002 TRACE event.

## Frozen identity

- shared_event_id: `iv002-shared-001`
- TRACE call_id: `iv002-shared-001`
- EABC command_id: `iv002-shared-001`
- temporal window: 2026-09-26T06:00:00Z ± 5 minutes

The identifier is agreed before either evidence artifact is generated and is independently recorded by both sides.

## EABC baseline

The governed action is:

```json
{"action":"set_value","target":"controlled_resource","value":42}
```

Its canonical SHA-256 is:

`sha256:df4166a3de4ab94628e90b53c20cf9027a6da2472e1eb131336ad83a24ea3e60`

## Cases

| Case | Controlled change | Expected |
|---|---|---|
| E1 | Same ID, same governed/executed payload | CORRELATED |
| E2 | Same ID, EABC post-gate transform changes executed value 42 → 43 | CORRELATED + EXECUTION_DIVERGENCE |
| E3 | CBA uses an unrelated expected TRACE call_id | UNRESOLVED |

E3 is deliberately an external negative-binding test. It does not mutate or impersonate the signed TRACE artifact.

## Anti-circularity

CBA is not authoritative. It is valid only if its hashes resolve to the supplied source artifacts and its binding rule is independently verified against fields contained in those artifacts.

The core check is:

`TRACE.call_id == EABC.command_id == CBA.shared_event_id`

For E3 the expected TRACE identifier in the CBA is deliberately different, so the equality fails and correlation remains unresolved.

## Claim boundary

The experiment demonstrates evidence correlation and separation of correlation from execution consistency. It does not establish that TRACE authorizes EABC, that EABC authorizes TRACE, causality from an identifier alone, production key management, or occurrence of a physical-world effect.
