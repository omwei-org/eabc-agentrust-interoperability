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

## AgenTrust's current boundary

The current AgenTrust cMCP embodied-action evidence profile separates three identifiers/evidence roles:

1. **`call_id`** — the cMCP audit-chain binding.
2. **`action_ref`** — a content-derived identifier for the requested action.
3. **external execution evidence / receipt** — an assertion from a controller or other external issuer.

The profile explicitly says that `linked_call_id` must remain the cMCP audit `call_id` and must not be overloaded with controller-specific `action_ref`. This is important for IV-002: the systems already tolerate multiple identities with different semantic scopes.

TRACE likewise separates session evidence, action issuance evidence, and external outcome evidence. A valid receipt proves the issuer's signed assertion and its binding; TRACE itself does not certify physical completion or functional safety.

IV-002 therefore does not need to invent a universal identifier. It needs a verifier-level rule for deciding when independently produced evidence objects refer to the same execution trajectory.

## Deliberate separation

The existing EABC binding relation may use an explicit call identifier when available.

IV-002 does not require every evidence producer to share that identifier.

The controlled test evaluates whether a relationship can instead be established from evidence dimensions such as:

- execution identity;
- action identity;
- temporal consistency;
- execution context;
- integrity/provenance.

This gives ARGUS a semantic distinction between:

- **bound** — evidence has a direct, verifiable binding;
- **correlated** — independent evidence can be shown to describe the same execution trajectory;
- **unresolved** — decisive binding evidence is missing;
- **contradictory** — evidence makes the proposed relationship untenable;
- **integrity failure** — evidence cannot safely support a correlation decision.

## E1–E6 interpretation

| Case | ARGUS interpretation |
|---|---|
| E1 | Sufficient independent evidence establishes one execution trajectory. |
| E2 | The trajectory correlates, but action application diverges from the committed/requested action. |
| E3 | The available evidence is insufficient to establish the relationship. |
| E4 | Contradictory evidence prevents the proposed relationship. |
| E5 | The trajectory correlates and the controller provides a valid negative outcome. |
| E6 | Integrity failure prevents a trustworthy correlation decision. |

The important property is that these are **different states**, not one generic "verification failed" result.

## Result

This gives the repository a two-level model:

1. **Execution binding** — EABC/T21/T25 evidence establishes what a commit is bound to.
2. **Cross-domain correlation** — IV-002 evaluates whether independently produced evidence can be reconstructed as one execution trajectory.

A positive result at level 2 does not imply authorization, consistency, safety, successful execution, or physical-effect verification.

## Claim boundary

The IV-002 test is controlled analytical instrumentation. It does not claim that TRACE and EABC currently expose a native production correlation contract.

The bridge remains explicit and separately inspectable.

The next production-grade step would be a real end-to-end fixture in which native AgenTrust action evidence and native EABC execution-boundary evidence are emitted independently for the same run, followed by ARGUS verification without a test-only bridge.
