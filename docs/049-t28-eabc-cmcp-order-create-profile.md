# T28 — EABC/cMCP Integration Profile: `order_create`

## Status

**Proposed interoperability profile**

This profile maps a concrete protected effect, `order_create`, onto existing cMCP/TRACE execution and evidence mechanisms.

It does **not** claim native EABC conformance of cMCP.

## Profile intent

The profile separates four questions that are often conflated:

1. Was an intent authorized?
2. Which execution was correlated to that intent?
3. What effect evidence can be linked to that execution?
4. Were all paths capable of producing the protected effect inside the declared execution boundary?

The first three have existing cMCP/TRACE mechanisms. The fourth is the EABC **Execution Scope** question.

## Mapping

| Property / Claim | Mapping | Assumptions | Gap | Evidence |
|---|---|---|---|---|
| **Authority binding** | Cedar supplies the authorization decision. A TRACE reference may bind an external grant with `rel: authorized-intent`. | The grant is independently identifiable and its scope matches the intended operation. | The reference does not itself establish complete mediation. | Cedar decision + TRACE authorized-intent reference. |
| **Effect correlation** | cMCP `execution_id` is a typed `AuditEntry` field and is carried on relevant evidence entries. TRACE can reference downstream effect evidence with `rel: observed-effect`. | The effect evidence is independently attributable to the correlated execution. | Correlation is not proof that an external effect occurred. | cMCP execution-correlation design; TRACE observed-effect relation. |
| **Execution binding** | cMCP Execution Action Binding v1 defines a canonical JCS binding over authenticated `agent_id`, `action_type`, `action_scope`, and `action_timestamp`, with the rendered digest used for execution correlation. | The binding contract is adopted and the integration maps action semantics without collapsing materially different operations. | The binding does not by itself provide exactly-once execution or external-effect proof. | cMCP Execution Action Binding v1. |
| **Protected Effect** | `order_create` is the protected effect for this profile instance. | The integration identifies the downstream operation/state mutation that constitutes order creation. | Downstream effect identity remains deployment-specific. | Concrete integration test/example. |
| **Execution Scope** | The profile declares the effect-producing paths that are claimed to be mediated. | The declared scope is complete for the claimed `order_create` effect domain and the boundary is exclusive. | **NOT CLAIMED by cMCP forwarding alone.** No existing cMCP field identified here represents the complete set/topology of all effect-producing paths. | Existing EABC/cMCP seam evidence establishes scoped MCP forwarding, not universal effect mediation. |
| **NON_BYPASSABILITY** | Conditional on the declared Execution Scope: every path capable of committing `order_create` must satisfy the applicable authority and execution conditions. | Complete mediation over the declared effect domain. | Cannot be claimed universally from gateway mediation alone. | EABC-MCP-007; execution-boundary tests. |

## Concrete execution chain

The profile-level evidence chain is:

```
authorized intent
      ↓
Cedar authorization decision
      ↓
execution action binding
      ↓
execution_id
      ↓
scoped order_create execution
      ↓
observed-effect reference
```

This chain is an interoperability mapping. It is not a claim that each arrow is natively an EABC primitive in cMCP.

## Execution Scope requirement

For an EABC claim of `NON_BYPASSABILITY(B,E)`, the relevant question is not:

> Does the cMCP gateway mediate MCP traffic?

The question is:

> For the declared `order_create` effect domain, does every path capable of committing the protected effect pass through the declared execution boundary and satisfy the required conditions?

A deployment may therefore claim a bounded execution scope, for example a specific application/API topology, while explicitly **NOT CLAIMING** universal mediation outside that topology.

## Conformance interpretation

A successful mapping of `execution_id`, authorization references, action binding, and observed-effect evidence does not by itself produce EABC conformance.

The profile result should distinguish:

- **MAPPED** — the concept has a direct existing cMCP/TRACE representation;
- **CONDITIONAL** — the mapping is valid only under a declared deployment assumption;
- **NOT CLAIMED** — the required evidence or representation is absent.

The expected result for the Execution Scope dimension is currently:

**CONDITIONAL / NOT CLAIMED**, until a concrete deployment can identify and evidence the complete effect-producing scope for `order_create`.

## Boundary

This profile does not define:

- Cedar policy syntax;
- cMCP transport behavior;
- a new cMCP wire field for Execution Scope;
- SLC implementation or substrate;
- EBP assurance levels;
- physical-world effect verification;
- exactly-once execution guarantees.

The purpose is narrower: establish a precise interoperability contract between EABC semantics and the cMCP/TRACE evidence surface, while making the remaining Execution Scope gap explicit.

## Relation to existing EABC-MCP profile

This profile extends the existing experimental EABC-MCP execution-seam profile by instantiating its abstract protected-effect and complete-mediation questions with the concrete `order_create` example.

It does not replace the existing profile and does not change its native/adapter boundary declaration.
