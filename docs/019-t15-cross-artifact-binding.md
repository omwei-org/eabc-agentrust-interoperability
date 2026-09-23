# 019 — T15 Cross-Artifact Binding Result

## Source baseline

cMCP commit `f8743e013786b094caaa70c336519834e73c74d5`.

T15 reconciles the actual cMCP artifacts identified in T10–T13.

### Artifact set

`AuditEntry` contains:

- `call_id`
- `tool_name`
- `policy_decision`
- `request_payload_hash`
- `execution_id`
- `prev_entry_hash`
- `entry_hash`

The complete AuditEntry is canonicalized and its `entry_hash` is SHA-256 over all fields except `entry_hash` itself. The chain is append-only and can be TEE-anchored.

The GatewayClaim is signed and contains session-level policy/runtime/chain evidence, while its privacy-preserving per-call transcript does not expose raw arguments.

## T15 interoperability mapping

| cMCP artifact | EABC adapter field | Status |
|---|---|---|
| `execution_id` | `execution_id` | DIRECT |
| `request_payload_hash` | `request_payload_hash` | DIRECT |
| policy bundle identity | `policy_bundle_hash` | DIRECT / profile mapping |
| tool name | `tool_name` | DIRECT |
| AuditEntry `entry_hash` | evidence reference | DIRECT |
| GatewayClaim signature | evidence authenticity | DIRECT |
| GatewayClaim chain root/tip | evidence continuity | DIRECT |
| `commit_id` | EABC `commit_id` | NO EXISTING cMCP FIELD |
| authority epoch | EABC `authority_epoch` | NO EXISTING cMCP FIELD |
| effect target identity | EABC `effect_target_id` | PARTIAL via server identity |

## New collaboration insight

The cMCP AuditEntry already provides a compact, privacy-preserving evidence tuple that can be carried into an EABC profile:

`execution_id + request_payload_hash + policy identity + tool_name + audit entry hash`

EABC does not need to duplicate the cMCP evidence layer.

Instead, the interoperability profile can define the missing semantic link:

`commit_id → AuditEntry.entry_hash`

with the commit itself binding the exact request hash and authority/policy state.

This yields:

`Cedar → EABC Commit → cMCP AuditEntry → GatewayClaim → TRACE/SCITT`

## Boundary that remains

The current cMCP AuditEntry is an excellent **evidence record**, but its existence does not make the corresponding forwarding event an EABC commit.

The collaboration target should therefore be a minimal **EABC Execution Commit Profile for MCP**, not a replacement for cMCP.

## Recommended experiment

Implement a profile adapter outside cMCP first:

`AuditEntry → EABC Commit Envelope → verification`

Then add a controlled enforcement hook at the forwarding seam and test:

1. commit envelope accepted → exact request forwarded;
2. digest mismatch → no forward;
3. policy identity mismatch → no forward;
4. authority version mismatch → no forward;
5. commit reference included in evidence.

This produces a concrete artifact AgenTrust can review without asking them to redesign cMCP.
