# 028 — T23 Full cMCP Call-Path Integration

## Objective

T23 moves the EABC gate from a standalone forwarding model into the real CMCPProxy.call_tool() path.

The test leaves cMCP production source unchanged. A disposable test wrapper replaces the forwarding method and applies the EABC commit gate at the actual call path.

## Path

CMCPProxy.call_tool()
→ request serialization
→ cMCP execution-admission behavior
→ health/catalog checks
→ sink policy
→ upstream drift check
→ Cedar policy evaluation
→ native cMCP ingress gateway
→ EABC commit gate
→ forwarding seam
→ mock effect

## Important finding

The cMCP runtime already performs several checks immediately before forwarding. The EABC gate therefore does not replace Cedar or the native gateway. It is an additional explicit condition at the forwarding seam.

The test uses cMCP's existing call_id and does not pass a caller-supplied execution_id.

## Test cases

### Valid

A prepared EABC commit with matching call_id, tool_name and request digest allows the call to reach the downstream effect stub.

### No commit

A normal cMCP call with no EABC commit is stopped at the EABC gate and produces no effect.

### Tampered request

A commit prepared for one argument set cannot authorize a changed argument set at the forwarding seam.

## Interpretation

T23 demonstrates the complete composition pattern in a disposable integration layer:

cMCP authorization/enforcement → EABC COMMIT → EFFECT

It does not claim that unmodified cMCP v0.5.0 contains this gate.

## Next step

Freeze the implementation experiment and produce the AgenTrust-facing collaboration artifact. The proposal should distinguish clearly between verified upstream behavior and the proposed EABC profile.
