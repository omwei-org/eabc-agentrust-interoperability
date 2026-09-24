# T29.5 — cMCP execution seam characterization

## Status

Characterized against cMCP commit f8743e013786b094caaa70c336519834e73c74d5. Native EABC integration is not claimed.

T29.5 tests the actual later cMCP execution-correlation revision rather than the T27 v0.5.0 pin.

## Observed production call path

CMCPProxy.call_tool(..., execution_id=...)
  -> _call_tool_impl(...)
  -> request serialization
  -> _check_execution_available(...)
  -> health/catalog/Cedar/gateway
  -> _forward_to_upstream(...)

The important result is that a supplied, syntactically valid execution_id currently does not enter the normal authorization/forwarding path.

The gateway returns execution_correlation_unavailable before health checks, catalog lookup, upstream discovery, Cedar authorization, or upstream invocation.

The upstream cMCP test suite explicitly verifies that behavior and verifies that _forward_to_upstream is not called.

## Consequence for EABC

This is a useful boundary characterization, not a failed EABC test.

The later cMCP revision has created an explicit execution-admission seam, but the seam is currently a fail-closed unavailable feature. It is not yet an operational execution-correlation contract that an EABC adapter can consume.

Therefore the proposed T29.2 chain cannot yet be exercised as a native runtime chain at this revision:

execution_id/action binding
  -> cMCP authorization
  -> EABC FINAL_AUTHORITY_CHECK
  -> EABC COMMIT
  -> forwarding

## Next integration target

1. A cMCP revision that activates execution correlation with a durable binding and terminal/audit contract; or
2. An explicit cMCP extension seam where an EABC execution admission/COMMIT result can be supplied immediately before _forward_to_upstream().

The direct collaboration question for AgenTrust is whether cMCP can expose the existing forwarding boundary as an explicit admission point while retaining its identity, Cedar, TEE, audit, and TRACE semantics.

## Claim boundary

This evidence does not establish native EABC support in cMCP, exclusive effect-path mediation, hardware-enforced EABC, exactly-once external execution, or proof of an external physical effect.

It establishes only the current software call-path behavior at the pinned revision.