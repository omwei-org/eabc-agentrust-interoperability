# T33 — Native Integration Contract

## Status

**PROPOSED CONTRACT — NOT NATIVE cMCP CONFORMANCE**

T33 defines the smallest transport-independent contract required for a future native cMCP/AgenTrust ↔ EABC integration.

T31 demonstrated the common production forwarding seam in the inspected pinned cMCP runtime.

T32 demonstrated execution-boundary exclusivity under two explicit profiles in a disposable runtime experiment.

Neither test establishes that upstream cMCP natively implements EABC. T33 therefore specifies the integration contract that would be required to make that relationship explicit and testable.

---

## 1. Purpose

The integration contract separates two decisions that must not be conflated:

1. **Authorization** — whether the authenticated principal is permitted by the applicable policy to request the action.
2. **Execution authority** — whether that already-authorized action may cross the execution boundary and become an effect under the current execution conditions.

The intended transaction is:

`INTENT → AUTHORIZATION → EXECUTION AUTHORITY → COMMIT → EFFECT`

For cMCP/AgenTrust interoperability:

`authenticated request → cMCP authorization → EABC execution admission → EABC COMMIT → existing cMCP forwarding → upstream consequence`

EABC does not replace identity, attestation, Cedar policy evaluation, audit, or TRACE. EABC supplies the execution-boundary semantics between an authorized action context and the forwarding transition that can cause the declared consequence.

---

## 2. Contract boundary

The native integration point SHALL be the existing cMCP forwarding transition.

The integration MUST NOT introduce a second forwarding path.

Conceptually:

`cMCP identity / attestation / authorization`
→ `AUTHORIZED ACTION CONTEXT`
→ `EABC EXECUTION AUTHORITY`
→ `COMMIT`
→ `existing forwarding transition`
→ `upstream consequence`

The EABC admission decision MUST occur immediately before the forwarding transition that is capable of causing the declared consequence.

For the inspected cMCP revision, that transition is the common `CMCPProxy._forward_to_upstream()` path used by the HTTP and stdio forwarding branches.

---

## 3. Inputs supplied by cMCP

cMCP supplies the authenticated and policy-authorized execution context.

The minimum action identity presented to EABC is:

| Field | Meaning | Owner / source |
|---|---|---|
| `agent_identity` | Authenticated execution principal | cMCP / AgenTrust |
| `execution_id` | Execution correlation identifier | cMCP / integration layer |
| `call_id` | Individual MCP call identity | cMCP |
| `tool_name` | Exact requested tool | cMCP |
| `request_payload_hash` | Canonical digest of the exact action payload | cMCP / integration layer |
| `policy_id` | Policy identity under which authorization was evaluated | cMCP / AgenTrust |
| `authority_ref` | Reference to the execution-authority state, when applicable | EABC authority domain |

### Important distinction

`execution_id` is a correlation identifier. It is **not itself execution authority**.

The EABC decision MUST bind the execution identifier to the exact action and to the current execution-authority state.

Likewise, a cMCP/Cedar `ALLOW` is an authorization result, not an EABC COMMIT.

---

## 4. EABC execution-admission contract

A native integration SHALL provide an abstract operation equivalent to:

`admit(action_context) → DENY | execution_commit`

The admission operation evaluates at least:

- exact action identity;
- authenticated execution identity;
- execution correlation;
- request payload identity;
- policy identity;
- current execution-authority state;
- validity of the requested authority;
- single-use commit/admission semantics.

A successful admission produces an execution commit bound to the action that is about to cross the boundary.

A failed admission MUST NOT permit the forwarding transition.

---

## 5. Commit binding

The EABC COMMIT MUST be bound to the exact execution tuple.

At minimum:

`agent_identity`
`execution_id`
`call_id`
`tool_name`
`request_payload_hash`
`policy_id`

The binding MUST be integrity-checked before forwarding.

The following substitutions therefore invalidate the commit:

- different agent identity;
- different execution ID;
- different call ID;
- different tool;
- different request payload;
- different policy identity.

A consumed commit MUST NOT be accepted for a second execution attempt.

The currently implemented experimental adapter demonstrates these binding and single-use properties. A future native contract may add stronger authority-state fields such as an authority epoch, but those are not claimed here as currently implemented by upstream cMCP.

---

## 6. Forwarding invariant

### Mandatory execution-boundary profile

For the strict profile:

`forwarded ⇒ successful EABC admission bound to the exact action`

Equivalently:

> No production-reachable tool call may enter the declared forwarding transition unless the corresponding EABC execution-admission contract has succeeded.

This is the profile that establishes EABC as an execution boundary for all tool calls.

### Optional interoperability profile

For backward-compatible operation:

`forwarded ⇒ execution_id absent OR successful EABC admission bound to the exact action`

A call without an execution ID is classified as:

**LEGACY_NON_CORRELATED**

It is not classified as an EABC bypass.

This profile allows existing non-correlated cMCP traffic to retain legacy forwarding semantics while execution-correlated traffic is subject to EABC admission.

---

## 7. Failure semantics

The integration MUST fail closed for execution-correlated calls when EABC admission cannot be established.

Examples include:

| Condition | EABC result | Forwarding |
|---|---|---|
| cMCP authorization denied | no admission | **NONE** |
| correlated request, no commit | deny | **NONE** |
| substituted call/tool/request/policy | deny | **NONE** |
| consumed/replayed commit | deny | **NONE** |
| current authority invalid/revoked | deny | **NONE** |
| valid authorization + valid EABC admission | commit | **ONE** |
| no execution ID, OPTIONAL profile | legacy | **ONE** |
| no execution ID, MANDATORY profile | deny | **NONE** |

The decisive boundary observable is the forwarding transition, not merely a downstream effect counter.

---

## 8. Evidence and audit correlation

cMCP remains responsible for its existing identity, authorization, attestation, audit, and TRACE functions.

The integration SHOULD correlate those records with the EABC execution transaction using:

- `execution_id`;
- `call_id`;
- EABC `commit_id`;
- action binding;
- authority reference.

This creates a traceable chain:

`authorization evidence → execution admission → commit → forwarding → consequence observation`

The presence of an audit record MUST NOT by itself be treated as proof that EABC execution authority was enforced. The enforcement boundary is the admission immediately preceding forwarding.

---

## 9. No second execution path

A native integration MUST preserve the existing cMCP forwarding implementation.

The integration point is a guard on the existing transition, not an alternative proxy or parallel forwarding implementation.

This preserves the T31 property:

> The inspected cMCP runtime has one identified common production forwarding transition for the declared HTTP and stdio tool-call consequences.

The native integration question is therefore not "where should EABC forward the request?" but:

> "What condition must be satisfied before cMCP is allowed to enter its existing forwarding transition?"

---

## 10. Architecture independence

The contract defines semantics, not deployment topology.

The EABC execution-authority implementation MAY be:

- an in-process library;
- a local service;
- a sidecar;
- a privileged execution component;
- a hardware-backed security layer / SLC;
- another implementation that provides equivalent execution-boundary semantics.

cMCP MUST NOT need to know the implementation mechanism in order to rely on the contract.

This preserves the separation:

**cMCP/AgenTrust:** identity, trust, attestation, authorization, audit, transparency.

**EABC:** execution authority, exact action binding, commit semantics, execution-boundary conditions.

**SLC / implementation:** enforcement mechanism for the execution boundary.

---

## 11. What T33 does and does not establish

### Established by preceding experiments

- T31: common forwarding seam identified in the inspected pinned cMCP runtime.
- T32: EABC admission can gate that seam in a disposable runtime experiment.
- T32: strict and backward-compatible execution-boundary profiles can be distinguished.
- T32: missing, substituted, and replayed execution commits can be prevented from reaching the forwarding transition in the experiment.

### Not established by T33

- native upstream cMCP support for EABC;
- a merged cMCP implementation of this contract;
- resistance to privileged code paths outside the inspected runtime;
- hardware isolation;
- distributed exactly-once semantics;
- physical-world effect enforcement.

T33 is therefore a **proposed native integration contract**, not a native conformance claim.

---

## 12. Minimal native conformance test

A future native implementation SHOULD be able to demonstrate the following property matrix against its production runtime:

| Test | Expected forwarding |
|---|---:|
| Authorization denied | 0 |
| Authorization allowed, EABC denied | 0 |
| Authorization allowed, valid EABC commit | 1 |
| Valid commit, substituted request | 0 |
| Valid commit, substituted tool | 0 |
| Valid commit, replay | 0 on second attempt |
| Revoked authority before forwarding | 0 |
| OPTIONAL profile, no execution ID | 1 |
| MANDATORY profile, no execution ID | 0 |

The critical test is not merely that the adapter can reject invalid inputs. It is that **the real production forwarding transition is unreachable unless the required execution-admission condition has succeeded**.

That is the native integration property T33 is intended to make explicit and testable.
