# 014 — T10 GatewayClaim Evidence Binding

## Source baseline

cMCP commit `f8743e013786b094caaa70c336519834e73c74d5`.

The normative GatewayClaim schema defines a signed envelope. The detached Ed25519 signature covers every field except the signature itself. The claim contains policy bundle hash, enforcement mode, runtime measurement, session identity, audit-chain root/tip/length, call totals, invoked tool names, and a privacy-preserving per-call transcript containing tool name, data class and decision.

## Critical finding

The schema's per-call transcript explicitly excludes raw parameters and response bodies.

Therefore the GatewayClaim signature cryptographically protects the **claim contents**, but the claim schema does not directly carry a per-call exact-request digest in the transcript.

The claim can therefore establish, for example:

`signed claim → tool X → allow → policy bundle H`

but the schema alone does not establish:

`signed claim → exact arguments A → exact upstream request digest D`

The audit chain may contain additional material, so this is a schema-level finding and not a claim that no implementation-side binding exists.

## T10 classification

| Evidence property | Result |
|---|---|
| GatewayClaim signed | DEMONSTRATED |
| Signature covers claim contents | DEMONSTRATED |
| Policy bundle hash included | DEMONSTRATED |
| Runtime measurement included | DEMONSTRATED |
| Session/audit-chain identity included | DEMONSTRATED |
| Per-call tool name included | DEMONSTRATED |
| Per-call decision included | DEMONSTRATED |
| Raw parameters in GatewayClaim transcript | ABSENT by schema |
| Per-call exact-request digest in GatewayClaim transcript | ABSENT by schema |
| Exact upstream request cryptographically bound by GatewayClaim schema | NOT DEMONSTRATED |
| Effect/outcome cryptographically bound | NOT DEMONSTRATED |

## EABC consequence

This gives a clean separation:

**GatewayClaim = signed session-level evidence + privacy-preserving call summary**

It should not automatically be mapped to EABC EAtt for exact execution binding.

A future interoperability profile could add an opaque `request_digest` / `commit_id` pair without exposing sensitive arguments:

`GatewayClaim → call_id → request_digest → EABC commit_id`

That would preserve the privacy property while making the execution-boundary relation independently verifiable.

## Next

T11 should inspect the implementation's audit-chain record for one allowed call and determine whether the exact request digest is already present there, even though it is intentionally omitted from the public GatewayClaim transcript.
