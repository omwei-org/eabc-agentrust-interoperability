# T25.4 — Failure-Path Binding Result

## Status

**PASS — independently validated against public cMCP v0.5.0**

Experiment revision: `47d043e97f7db5a230c87da5e42d99c8b9b696b8`  
CI run: `35838847022`  
cMCP source: public `v0.5.0`

## Question

Can cMCP's existing finalization/effect-boundary state distinguish an EABC COMMIT followed by a definitely-not-attempted downstream operation from a COMMIT followed by an operation whose outcome may be unknown?

## Observed behavior

The tests exercised the real `CMCPProxy.call_tool()` path and a disposable forwarding seam.

| Scenario | cMCP state | Expected disposition | Result |
|---|---|---|---|
| Failure before transport | `PRE_TRANSPORT` | `not_attempted` | PASS |
| Transport may have started | `TRANSPORT_MAY_HAVE_STARTED` | `outcome_unknown` | PASS |
| Cancellation after transport may have started | `TRANSPORT_MAY_HAVE_STARTED` | `outcome_unknown` | PASS |

## EABC interpretation

This demonstrates that cMCP has a useful execution-boundary state model for distinguishing:

- COMMIT followed by no downstream transport attempt;
- COMMIT followed by a potentially started downstream operation with unknown final outcome.

This is directly relevant to EABC failure semantics because a post-COMMIT transport failure must not automatically be interpreted as proof that the external effect did not occur.

## What this does NOT prove

T25.4 does **not** prove:

- native EABC COMMIT semantics in unmodified cMCP;
- that `eabc_commit_id` is persisted in the production AuditEntry;
- that cMCP can independently prove whether the downstream effect occurred;
- universal/exclusive mediation;
- physical or hardware enforcement.

T25.3 established that the production terminal audit can reconstruct the cMCP execution tuple but does not natively serialize the EABC commit identity.

## Conclusion

**T25.4 PASS: cMCP's existing finalization model is compatible with EABC-style failure classification at the forwarding boundary.**

The remaining interoperability requirement is explicit binding:

`EABC commit_id + call_id + request_digest + outcome_state → durable evidence`

Without that binding, cMCP can describe the execution attempt and its boundary state, but cannot by itself establish which EABC COMMIT authorized the attempt.

