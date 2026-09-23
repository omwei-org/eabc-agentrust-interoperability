# 007 — T04 Execution Correlation Boundary

## New finding

Upstream cMCP v0.5.0 contains explicit execution-correlation handling.

The upstream test suite demonstrates that when an `execution_id` is supplied but execution correlation is unavailable, the proxy fails closed and does not forward the tool call.

This is materially relevant to EABC because it introduces an execution identity between the policy path and the upstream effect path.

## EABC interpretation

This should not yet be called a full EABC commit.

The observed property is narrower:

`execution_id supplied + correlation unavailable → DENY + NO_FORWARD`

That is evidence for scoped execution-path control and failure semantics.

It does not by itself prove:

`authorized request == committed request == executed effect`

because the test establishes refusal when correlation is unavailable, not a cryptographically or atomically bound commit object.

## Classification

| EABC concern | Result |
|---|---|
| Execution correlation concept exists | DEMONSTRATED |
| Missing execution correlation fails closed | DEMONSTRATED |
| No upstream forwarding on correlation failure | DEMONSTRATED |
| Execution identity bound to exact authorized request | PARTIAL / requires experiment |
| Atomic authority-to-effect commit | NOT DEMONSTRATED |
| Physical effect binding | NOT DEMONSTRATED |

## Next experiment

Exercise a real HTTP `MCPServer(proxy).app` path with a valid execution identity and a capture endpoint, then inspect the resulting audit entry and upstream request together.

The key question becomes whether cMCP's execution identity is merely a correlation/audit identifier or participates in an enforceable commit-time binding.
