# IV-002 — Integration with the existing evidence-binding model

IV-002 is deliberately layered on the repository's existing evidence-binding work rather than introducing a second binding framework.

## Existing basis

T21 establishes commit-to-call correlation using:

- call identity;
- tool identity;
- request payload digest;
- policy bundle hash;
- terminal evidence reference.

T25.7 makes the EABC commit binding durable and content-addressed through a deterministic evidence hash.

These mechanisms are useful inputs to IV-002, but IV-002 asks a different question.

## IV-002 question

T21/T25 establish whether a particular EABC commit can be bound to an execution-side evidence record.

IV-002 asks whether independently produced evidence objects can be correlated across domains while preserving uncertainty, contradiction, rejection, divergence, and integrity failure as distinct outcomes.

Therefore IV-002 is an assurance/correlation layer over evidence, not a replacement for the existing EABC binding contract.

## Deliberate separation

The existing EABC binding relation may use an explicit call identifier when available.

IV-002 does not require every evidence producer to share that identifier.

The controlled test evaluates whether a relationship can instead be established from evidence dimensions such as execution identity, action identity, temporal consistency, execution context, and integrity/provenance.

## Result

This gives the repository a two-level model:

1. **Execution binding** — EABC/T21/T25 evidence establishes what a commit is bound to.
2. **Cross-domain correlation** — IV-002 evaluates whether independently produced evidence can be reconstructed as one execution trajectory.

A positive result at level 2 does not imply authorization, consistency, safety, successful execution, or physical-effect verification.

## Claim boundary

The IV-002 test is controlled analytical instrumentation. It does not claim that TRACE and EABC currently expose a native production correlation contract.

The bridge remains explicit and separately inspectable.
