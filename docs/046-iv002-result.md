# IV-002 — Cross-Domain Evidence Correlation Result

## Result

IV-002 completed a controlled analytical test across E1–E6 using a real AgenTrust TRACE artifact and a real EABC Run 004 artifact as evidence inputs.

The cross-domain relationship used for E1/E2 was explicitly constructed as a test bridge. It is not a new TRACE or EABC production format.

## Test matrix

| Case | Observed result |
|---|---|
| E1 — Nominal | **CORRELATED** |
| E2 — Divergence | **CORRELATED + EXECUTION_DIVERGENCE** |
| E3 — Missing binding | **UNRESOLVED** |
| E4 — Contradiction | **NOT_CORRELATED** |
| E5 — Controller rejection | **CORRELATED + REJECTED** |
| E6 — Integrity failure | **INTEGRITY_FAILURE / UNDETERMINED** |

## Principal finding

> **The requirement is the provable relationship, not a common identifier convention.**

ARGUS does not require a convention such as:

`TRACE.call_id == EABC.command_id`

Correlation can instead be established from independently observable relationships across execution identity, action identity, temporal consistency, execution context, and integrity/provenance.

## AgenTrust seam confirmed

Current AgenTrust embodied-action evidence work makes the boundary explicit:

- cMCP `call_id` binds external execution evidence to the gateway audit entry;
- `action_ref` is a separate content-derived identifier for the action request;
- controller receipts are external outcome evidence;
- TRACE action-receipt verification does not by itself prove physical completion or safety.

Therefore IV-002 does not introduce a competing receipt model. It evaluates how an EABC execution-boundary evidence plane can be related to the existing AgenTrust evidence planes.

## Separation of concerns

**TRACE / cMCP → governed session and action evidence**

**EABC → execution-authority / commit / execution-boundary evidence**

**Independent controllers and monitors → outcome observations**

↓

**ARGUS → correlation / reconstruction / assurance**

The experiment therefore supports an assurance-plane model in which TRACE/cMCP and EABC can remain semantically independent evidence producers.

## Important distinction

E2 demonstrates:

**CORRELATED + EXECUTION_DIVERGENCE**

The evidence can identify a common execution trajectory while showing:

**committed action ≠ applied action**

Therefore correlation must remain distinct from execution consistency, authorization, safety, successful execution, and physical-effect verification.

E5 similarly demonstrates that a valid controller rejection is not the same thing as a correlation failure:

**CORRELATED + REJECTED**

This preserves negative outcome evidence rather than erasing the execution relationship.

## Claim boundary

This result supports the architecture hypothesis under a controlled test.

It does **not** establish native TRACE × EABC production interoperability.

The cross-domain relationship was explicitly constructed as analytical test instrumentation. Production interoperability, physical-effect verification, and bypass resistance remain outside the scope of this result.

The current AgenTrust TRACE specification is a developer-preview specification (v0.2); IV-002 therefore treats its semantics as the current external reference, not as a frozen production standard.
