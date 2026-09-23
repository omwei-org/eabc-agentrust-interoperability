# 004 — T03 Request Substitution

## Question

Can request parameters change between cMCP authorization and the forwarding seam?

## Current result

T03 tests the real `CMCPProxy` path and observes that request A reaches the forwarding seam unchanged. This is an execution-path observation, not yet proof of downstream execution binding.

## Classification

| Property | Result |
|---|---|
| Authorization of A | DEMONSTRATED at proxy seam |
| A reaches forwarding seam | DEMONSTRATED |
| A equals forwarded request | DEMONSTRATED |
| A equals downstream executed request | NOT DEMONSTRATED |
| Substitution B is prevented against an adversarial transport | NOT DEMONSTRATED |

## Next step

Replace the forwarding mock with a local mock MCP server and compare the digest of the authorized request with the exact JSON-RPC/tool payload actually received upstream.
