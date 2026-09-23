# 006 — T03 Real cMCP Transport

## Result

The experiment exercises the real CMCPProxy.call_tool() path from authorization through cMCP forwarding to a local execution-domain HTTP endpoint.

Observed path:

policy allow → CMCPProxy → _forward_to_upstream → HTTP → capture server

The capture server records the received JSON-RPC payload and its wire SHA-256.

The test constructs the expected cMCP wire request with the upstream cMCP build_request() function and compares it with the request actually received.

## Classification

| Property | Result |
|---|---|
| cMCP policy path exercised | DEMONSTRATED |
| cMCP real forwarding implementation exercised | DEMONSTRATED |
| execution-domain endpoint actually received request | DEMONSTRATED |
| authorized tool/arguments == received tool/arguments | DEMONSTRATED |
| cMCP request construction == received JSON-RPC request | DEMONSTRATED |
| universal execution binding | NOT DEMONSTRATED |
| adversarial request substitution prevention | NOT DEMONSTRATED |
| downstream physical effect binding | NOT DEMONSTRATED |

## Interpretation

This is the first transport-level interoperability result. It establishes a concrete scoped chain from the cMCP authorization path to an execution-domain endpoint.

It does not establish the full EABC invariant for an independently controlled execution domain, because the endpoint is cooperative and the test does not attempt to alter the request after authorization.

Next: adversarial substitution at the transport boundary.
