# 012 — T08 Policy Mutation / Configuration Binding

Source baseline: cMCP v0.5.0 commit `f8743e013786b094caaa70c336519834e73c74d5`, including its policy hot-reload specification.

## Finding

cMCP has an implemented policy hot-reload mechanism. `PolicyEvaluator.evaluate()` invokes the policy store reload path, and the runtime can install a new signed policy bundle without restart when a signing key is pinned. The new bundle is versioned and its signature is checked against the pinned policy signing key.

This is materially stronger than the previously observed "startup-only policy" model.

## EABC interpretation

Policy mutation is therefore not ABSENT.

The relevant distinction is:

- **policy configuration freshness**: cMCP has a runtime mechanism;
- **authority epoch at commit**: not demonstrated;
- **atomic binding of exact request + authority state + commit**: not demonstrated.

A policy bundle hash is included in the evidence path, and reload causes the runtime measurement binding to be refreshed. This gives a verifier evidence of which policy bundle was active for a call.

However, a changed policy bundle does not by itself establish that an already-authorized request has an explicit commit-time reservation under the old or new authority epoch.

## T08 result

| Question | Result |
|---|---|
| Runtime policy reload exists | DEMONSTRATED |
| New policy can be authorized without restart | DEMONSTRATED, signing-key mode |
| New policy authenticity is checked | DEMONSTRATED |
| Version/downgrade control exists | DEMONSTRATED |
| Policy bundle hash changes across versions | DEMONSTRATED |
| Evidence records active policy identity | DEMONSTRATED |
| Explicit authority epoch | NOT DEMONSTRATED |
| Existing prepared request has a commit-time authority reservation | NOT DEMONSTRATED |
| Atomic policy-state + exact-request commit | NOT DEMONSTRATED |
| External effect binding to policy commit | NOT DEMONSTRATED |

## Critical consequence

T08 does **not** establish a TOCTOU failure.

It establishes that cMCP has a meaningful configuration transition mechanism, but the audited public contract does not expose an EABC-style atomic transition:

`prepared_under_H1 → H2 → commit → stale(H1)`

Therefore the correct EABC classification remains NOT DEMONSTRATED for commit-time authority freshness.

## Next experiment

T09 should test the one remaining boundary question directly:

**Can a request evaluated under policy H1 still be forwarded after H2 becomes active, or is the request always re-evaluated after the transition?**

This requires a controlled pause between authorization and forwarding. If the current cMCP call path has no such hook, the correct result is an architecture/source finding rather than an invented vulnerability.

