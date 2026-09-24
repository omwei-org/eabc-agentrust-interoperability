# T29 — cMCP Forwarding-Path Bypass Experiment

## Status

**Boundary experiment — no cMCP vulnerability claim**

T29 tests the exact question left open by T28:

> Can the declared MCP-forwarding consequence occur without passing through the EABC-controlled commit gate?

The experiment separates the **public cMCP call path** from a deliberately invoked **internal forwarding primitive**.

## Test model

Public path:

```
CMCPProxy.call_tool()
  → cMCP checks
  → EABC adapter gate
  → _forward_to_upstream()
  → upstream effect
```

The T29 adapter is intentionally installed at the existing forwarding seam, as in T19–T27.

The experiment has three cases:

1. **No commit through public path** — must be rejected before the forwarding effect.
2. **Valid commit through public path** — matching execution reaches the forwarding effect.
3. **Direct internal forwarding call** — deliberately invokes `_forward_to_upstream()` without `call_tool()`.

## Why case 3 matters

Case 3 demonstrates an important architectural fact:

**The EABC property is not created merely by the existence of a forwarding function.**

If another execution path can directly invoke the underlying forwarding primitive, that path is outside the adapter gate.

However, this is **not by itself a cMCP bypass vulnerability**. The test directly calls a Python internal method that is not the public MCP request entrypoint. It therefore proves only that the experimental adapter does not instrument every possible in-process call to the primitive.

A real cMCP bypass claim would require a reachable production execution path that:

- is available to the relevant adversary;
- can cause the same declared consequence;
- avoids the EABC gate;
- does not require modifying the test harness or privileged internal state.

## Interpretation

Expected result:

| Case | EABC commit | Effect | Interpretation |
|---|---|---|---|
| Public call, absent commit | No | No | Adapter gate works |
| Public call, exact commit | Yes | Yes | MAY → COMMIT → effect works experimentally |
| Direct internal method call | No | Yes | Adapter is not a universal in-process interposition mechanism |

This is a **useful negative result**, not a failure of T29.

It tells us exactly what must be demonstrated before claiming exclusive mediation:

> Every production-reachable path capable of causing the declared MCP-forwarding consequence must pass through the same controlled commit boundary.

## T29 conclusion boundary

T29 does **not** establish:

- native cMCP EABC conformance;
- privileged-bypass resistance;
- hardware-enforced exclusive mediation;
- physical-world execution authority;
- a security vulnerability in cMCP.

T29 does establish the narrower experimental distinction between:

- **public gateway-path mediation**, and
- **universal in-process mediation**.

The next meaningful step is therefore not to test more Python call variants. It is to enumerate the **production ingress paths** capable of invoking an upstream tool and determine whether any such path reaches the effect without `CMCPProxy.call_tool()`.

If no relevant production path exists, the direct internal-call result is merely an implementation-boundary observation.

If a relevant externally reachable path exists, that path becomes the actual bypass candidate.
