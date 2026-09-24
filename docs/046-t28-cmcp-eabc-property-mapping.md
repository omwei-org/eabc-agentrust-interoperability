# T28 — cMCP → EABC Property Mapping v1

## Status

**Analytical mapping — no native-conformance claim**

T28 maps the EABC execution-authority properties against the observed cMCP v0.5.0 architecture and the existing T19–T27 interoperability evidence.

The purpose is to identify which properties are already represented by cMCP artifacts or enforcement, which are candidates requiring semantic verification, and which remain unproven.

This document does not claim that cMCP v0.5.0 natively implements EABC.

## Reference boundary

The mapping uses the cMCP tool-call path:

```
Agent
  ↓
CMCPProxy.call_tool()
  ↓
cMCP identity / request processing
  ↓
Cedar authorization inside TEE
  ↓
egress / response policy checks
  ↓
upstream forwarding
  ↓
MCP tool effect
  ↓
AuditEntry
  ↓
GatewayClaim / TRACE
```

The existing EABC interoperability seam is the adapter/commit gate immediately before the cMCP upstream forwarding operation.

T19 established that `CMCPProxy._forward_to_upstream(call_id, entry, tool_name, arguments)` is a concrete runtime seam. T20/T21 established that the interoperable correlation should use cMCP's existing `call_id` rather than introduce a caller-supplied `execution_id`.

## Property mapping

| EABC property | cMCP mechanism / artifact | Status | What remains to prove |
|---|---|---|---|
| Relevant state evidence | TEE attestation, GatewayClaim / TRACE | **Mapped** | Scope and freshness requirements for the authority decision |
| Authorization | Cedar policy evaluation | **Mapped** | Exact semantics of the authorization grant at COMMIT time |
| Policy identity | Policy bundle hash measured/recorded by cMCP | **Mapped** | Binding to the exact policy material used by the EABC commit |
| Independent enforcement | Cedar enforcement inside TEE | **Mapped** | The TEE protects the cMCP enforcement component; this does not by itself prove consequence exclusivity |
| Complete mediation | cMCP intercepts MCP tool calls sent through the gateway | **Strong candidate / scoped** | Must define the declared effect domain; MCP mediation must not be generalized to universal effect mediation |
| Exact request binding | cMCP request payload hash + EABC commit binding | **Demonstrated by adapter** | Production/native enforcement of the binding remains unclaimed |
| Context/state binding | `call_id`, tool identity, request hash, policy identity | **Demonstrated by adapter** | Final authority freshness semantics at the native cMCP boundary |
| Deterministic commit | EABC adapter commit gate before forwarding | **Demonstrated experimentally** | Native cMCP must not be treated as enforcing EABC COMMIT semantics without an integration layer |
| Single-use commit | T25 replay test | **Demonstrated by adapter** | Native cMCP semantics do not currently expose this as an EABC primitive |
| Failure semantics | cMCP enforcing mode returns structured denial; EABC profile distinguishes pre-transport / unknown / terminal states | **Mapped + extended** | Exact boundary semantics for ambiguous downstream outcomes |
| Evidence continuity | AuditEntry → GatewayClaim / TRACE; T21 commit→call→entry correlation | **Demonstrated experimentally** | Native exposure of the EABC relation is not claimed |
| Execution evidence | `external_execution_evidence`, embodied-action evidence profile | **Mapped** | External receipt does not itself establish physical effect truth |
| Exclusive effect-path mediation | cMCP gateway is the controlled MCP forwarding path | **UNPROVEN** | Whether the declared consequence can occur without passing through the controlled commit boundary |
| Consequence-bounded authority | Final authority immediately before irreversible effect | **UNPROVEN** | The actual consequence boundary must be declared for each effect domain |

## Critical distinction: mediation domain

cMCP provides a strong gateway-level mediation property for MCP traffic. That is not equivalent to proving that cMCP exclusively mediates every path to a real-world consequence.

Therefore an EABC profile MUST declare an effect domain.

Examples:

- **MCP request domain:** whether a tool invocation reaches the upstream MCP server.
- **Controller handoff domain:** whether an authorized action is handed to an external controller.
- **Physical actuation domain:** whether a physical-world action becomes committed.

The first can be tested directly at the cMCP forwarding seam.

The latter two require an independently specified downstream boundary and evidence source.

## TEE effect

Putting cMCP inside a TEE strengthens the mapping for:

- code integrity of the governed runtime;
- integrity of the policy enforcement component;
- protection of policy/configuration measurement;
- resistance to modification by the governed host/process.

It does **not**, by TEE placement alone, establish:

- authorization standing for a particular consequence;
- exclusive mediation of every path to that consequence;
- physical execution truth;
- EABC COMMIT semantics.

TEE therefore strengthens **independent enforcement**, but the EABC question remains consequence-boundary specific.

## Current conclusion

The existing T19–T27 work already demonstrates an experimental EABC adapter at the cMCP forwarding seam.

T28 identifies the remaining semantic gap more precisely:

> **The unresolved property is not whether cMCP can enforce a policy, nor whether its enforcement can be attested. The unresolved property is whether the declared consequence is exclusively committed through the EABC-controlled boundary.**

Accordingly, the next experiment should not add another evidence format.

It should test the strongest remaining claim:

```
valid authorization
      +
exact execution binding
      +
fresh final authority
      +
exclusive commit path
      ↓
irreversible consequence
```

The first practical target should remain the **MCP forwarding consequence**, because that is the boundary directly exposed by cMCP v0.5.0 and already exercised by T19–T27.

## Relationship to AgenTrust

This mapping preserves the existing cMCP architecture:

- AgenTrust/cMCP retains Cedar authorization;
- TEE retains protected enforcement and attestation;
- TRACE/GatewayClaim retains evidence;
- EABC adds an experimentally testable execution-commit relation at the declared consequence boundary.

No replacement of Cedar, TEE attestation, GatewayClaim, TRACE, or cMCP audit semantics is required by this mapping.

## Claim boundary

T28 establishes an analytical mapping, not conformance.

The resulting status is:

**EABC ↔ cMCP interoperability: experimentally demonstrated at the adapter/forwarding seam.**

**Native cMCP EABC conformance: NOT_CLAIMED.**

**Exclusive mediation of a declared downstream physical consequence: NOT_YET_ESTABLISHED.**
