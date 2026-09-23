# 018 — T14 EABC × AgenTrust Commit Adapter

## Purpose

T14 is the first interoperability prototype rather than a cMCP defect test.

It defines the smallest adapter needed to turn existing cMCP/AgenTrust artifacts into an explicit EABC-style commit envelope.

The adapter does not replace Cedar, cMCP enforcement, or TRACE. It binds their outputs at a named commit point.

## Commit envelope

`commit_id`
`execution_id`
`request_payload_hash`
`policy_bundle_hash`
`authority_epoch`
`tool_name`

The exact field set is experimental and is not proposed as an AgenTrust standard.

## Required invariants

1. no commit → no effect;
2. wrong request digest → no effect;
3. stale authority → no commit;
4. stale policy → no commit;
5. valid commit → exact request reaches effect seam.

## Why this is the collaboration surface

AgenTrust/cMCP already owns the policy, identity, TEE and evidence layers. EABC contributes an explicit execution-commit semantic.

The prototype therefore tests composition, not replacement.

## Scope

This is an independent harness. It does not claim that cMCP v0.5.0 currently exposes an `authority_epoch` or an EABC `commit_id`. Those are adapter-level concepts used to make the missing semantic explicit.

## Expected next phase

Run T14 in CI, produce machine-readable evidence, then build a second adapter that consumes actual cMCP artifacts:

`Cedar decision + policy hash + execution_id + request_payload_hash → EABC commit envelope → GatewayClaim/TRACE`

The next test should then verify cross-artifact equality rather than only adapter-internal behavior.
