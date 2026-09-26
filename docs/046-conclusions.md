# T27 — Conclusions

The T25–T27 work was intended to determine how far the EABC execution-boundary model can be reduced to an existing software gateway model represented by cMCP.

## Primary result

The strongest identified capability difference is **universal effect mediation**.

cMCP provides exclusive mediation within its declared MCP forwarding topology. The gateway can control the MCP traffic that is routed through it, but this does not establish that every possible path to a protected downstream effect must pass through the gateway.

The T25.9 reducibility matrix therefore classifies:

| EABC property | cMCP v0.5.0 classification |
|---|---|
| Exclusive mediation | PARTIAL / scope-bounded |
| Universal effect mediation | ABSENT / NOT CLAIMED |

The distinction is architectural:

```text
Declared MCP topology:

agent → cMCP gateway → upstream MCP server → effect
             ↑
       mediation point
```

This does not establish:

```text
all principals / processes / network paths
                    ↓
             execution boundary
                    ↓
                  effect
```

The cMCP-side limitation is also consistent with AgenTrust's own discussion of deny-based Cedar enforcement versus short-lived, minimal-scope credentials. Issue #554 explicitly distinguishes a policy decision at a gateway chokepoint from an authority that constrains what the principal can do at all.

## EABC property

EABC defines **Complete Mediation** as an execution-boundary requirement: the protected effect domain is mediated by the execution boundary rather than only by a declared application gateway topology.

This is a normative EABC property.

This experiment does **not** establish that a particular SLC deployment already provides universal mediation over every possible physical or logical path to an effect. That requires independent validation of the concrete execution-boundary architecture.

## Secondary differences

The reducibility work also identified several properties with weaker evidence classifications:

| EABC property | cMCP observation | Classification |
|---|---|---|
| ECT | request, call identity, tool and policy context exist, but exact committed execution-object semantics are not native | PARTIAL |
| EAtt / commit evidence | terminal audit exists, but native EABC commit identity is absent | PARTIAL |
| PREPARE / FINAL_AUTHORITY_CHECK / COMMIT separation | Cedar evaluation and downstream enforcement exist, but the EABC three-stage separation is not native | PARTIAL / different semantics |
| Dynamic freshness | `action_timestamp` is bound into the action digest; this is not equivalent to EABC decision-time freshness evaluation | different semantics |
| Domain/version binding | cMCP EAB binds domain and version into its cryptographic preimage; equivalence to EABC contract/profile identity is not established | different semantics |

These findings are not classified as capability gaps. They identify semantic differences or partial reductions.

## What the adapter demonstrated

The interoperability adapter demonstrates that selected EABC properties can be imposed at a cMCP forwarding seam, including:

- exact execution binding;
- explicit EABC COMMIT identity;
- substitution rejection;
- replay rejection;
- COMMIT-to-terminal-audit binding.

This demonstrates software interoperability at the tested seam.

It does not establish native EABC conformance of unmodified cMCP.

## Architectural conclusion

The experiment does not show that software gateways are incapable of performing EABC-related functions.

It shows a more specific boundary:

> **An application-level software gateway can mediate the execution paths within the topology it controls, but gateway mediation alone does not establish universal mediation of all possible paths to the protected effect.**

EABC places Complete Mediation at the execution boundary rather than treating application-gateway mediation as equivalent to universal effect mediation.

## Claim boundary

The evidence supports the following claims:

- cMCP v0.5.0 provides substantial authorization, enforcement, attestation, audit, and execution-correlation capabilities.
- Selected EABC semantics can be integrated with cMCP through an adapter.
- cMCP's mediation is scoped to its declared MCP forwarding topology.
- Universal effect mediation is classified **ABSENT / NOT CLAIMED** for the tested cMCP scope.
- EABC defines Complete Mediation as an execution-boundary property.

The evidence does not establish:

- native EABC conformance of unmodified cMCP;
- universal mediation by a particular SLC deployment;
- physical isolation of every possible downstream effect path;
- privileged-bypass resistance of a concrete hardware implementation;
- physical-world effect verification.

## Overall result

**SOFTWARE-GATEWAY LIMIT IDENTIFIED**

The experiment identified a concrete architectural property for which the tested cMCP gateway model does not provide an equivalent: **universal effect-path mediation**.

The EABC/SLC execution-boundary model explicitly defines this property, but validation of the property on a concrete SLC implementation remains a separate claim.
