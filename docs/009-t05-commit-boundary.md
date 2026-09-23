# 009 — T05 Commit Boundary Harness

## Objective

Translate the observed cMCP execution path into an EABC-style commit experiment without modifying cMCP.

The harness models the boundary explicitly:

1. PREPARE — construct the exact request and its canonical digest.
2. FINAL_AUTHORITY_CHECK — re-check the authority epoch immediately before commit.
3. COMMIT — create a commit record binding request digest, execution identity, and authority epoch.
4. EFFECT — only the committed request may be delivered to the execution-domain endpoint.

## Test vectors

- T05-A: allow → prepare → commit → effect.
- T05-B: prepare → authority epoch changes → commit refuses.
- T05-C: prepare request A → commit request B → refuses.
- T05-D: committed A → attempted downstream B → execution-binding violation.

## Important interpretation

This harness is an **independent EABC reference experiment**, not a claim that cMCP v0.5.0 already implements this commit contract.

The purpose is to determine which parts can be mapped onto cMCP's existing execution correlation/action-binding concepts.

Current cMCP evidence supports request forwarding, fail-closed execution correlation, and an action-level evidence convention. The cMCP project itself describes its embodied-action profile as evidence binding rather than actuation or safety certification. citeturn0search3

## Success criterion

The key invariant is:

`authorized_request_digest == committed_request_digest == delivered_request_digest`

with:

`commit_authority_epoch == current_authority_epoch`

at commit time.

A failure must produce no execution-domain delivery.
