# 013 — T09 Policy Transition Race

## Source audit

Baseline: cMCP commit `f8743e013786b094caaa70c336519834e73c74d5`.

The policy evaluator calls `_maybe_reload()` at the beginning of `evaluate()`. A changed bundle is installed before Cedar evaluation, and the resulting decision is then returned as a `PolicyDecision`.

The audited call path does not expose a second Cedar evaluation immediately before upstream forwarding. Therefore the relevant transition is:

`policy reload → Cedar evaluation → PolicyDecision → downstream enforcement/forwarding`

rather than:

`policy reload → evaluation → policy reload → final evaluation → commit`.

## T09 result

The experiment establishes a source-level architectural fact, not a vulnerability:

- policy changes are observed at evaluation entry;
- the decision is produced from the bundle active at that evaluation;
- policy reload is not itself an EABC commit-time authority reservation;
- no explicit authority epoch is carried from evaluation into a later commit gate;
- the public path does not demonstrate a second policy-state check at the exact forwarding point.

## Classification

| Property | Result |
|---|---|
| Policy transition mechanism | DEMONSTRATED |
| Reload before evaluation | DEMONSTRATED |
| Evaluation uses current loaded bundle | DEMONSTRATED |
| Decision carries policy decision semantics | DEMONSTRATED |
| Explicit policy epoch in commit object | NOT DEMONSTRATED |
| Second authorization check immediately before forwarding | NOT DEMONSTRATED |
| Atomic policy-state + request commit | NOT DEMONSTRATED |
| Demonstrated TOCTOU exploit | NOT DEMONSTRATED |

## Important interpretation

This must not be described as a confirmed TOCTOU vulnerability. A race would require a specific externally reachable interleaving in which policy state changes after the relevant authorization decision and before an effect that remains authorized by that stale decision.

The current evidence establishes only that the policy reload boundary and the forwarding boundary are separate concepts.

## EABC consequence

T09 strengthens the reducibility matrix:

`cMCP policy freshness ≠ EABC commit-time authority binding`

cMCP has meaningful runtime policy freshness and fail-closed controls. EABC adds an explicit semantic point at which authority, exact request, and execution commitment are jointly fixed.

## Next

T10 should examine the evidence object produced for an allowed call and determine exactly which request fields, policy identity, execution identity, and decision data are cryptographically bound into the GatewayClaim.

That moves the audit from **control path** to **evidence binding**.
