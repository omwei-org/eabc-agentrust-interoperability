# 016 — T12 Request Hash Placement

## Source baseline

cMCP commit `f8743e013786b094caaa70c336519834e73c74d5`.

The real `CMCPProxy._call_tool_impl()` computes `request_payload_hash` at the beginning of the call, before execution-correlation admission, health checks, catalog lookup, Cedar evaluation, cMCP ingress interception, or upstream invocation.

The hash is calculated from the canonical JSON serialization of the **arguments object**:

`json.dumps(arguments, sort_keys=True, separators=(",", ":"))`

The same hash is subsequently supplied to terminal audit records across the call path.

## T12 result

This establishes that the request hash is **pre-decision and pre-forwarding evidence**, not merely a post-hoc hash generated after the effect.

Observed ordering:

`arguments → SHA-256 → finalization.request_payload_hash → admission/evaluation → forwarding → terminal audit`

The upstream forwarding code constructs a separate MCP JSON-RPC request containing:

- call ID
- method
- tool name
- arguments
- parameter-derived headers

The audited hash covers the arguments object only, not the complete JSON-RPC envelope or transport headers.

## Classification

| Property | Result |
|---|---|
| Hash created before authorization | DEMONSTRATED |
| Hash created before forwarding | DEMONSTRATED |
| Same hash carried into terminal audit | DEMONSTRATED |
| Hash covers canonical tool arguments | DEMONSTRATED |
| Tool name separately identified | DEMONSTRATED |
| Full JSON-RPC request covered by hash | NOT DEMONSTRATED |
| Call ID covered by request hash | NOT DEMONSTRATED |
| Transport headers covered by request hash | NOT DEMONSTRATED |
| Hash is itself a commit authorization | NOT DEMONSTRATED |
| Hash is bound to an execution commit event | NOT DEMONSTRATED |
| Hash is bound to external effect | NOT DEMONSTRATED |

## Important consequence

T12 materially strengthens the interoperability case.

The request hash exists **before** the decision and effect path, so it can serve as an input to a future EABC binding without changing the privacy model.

But the current implementation does not show that the immutable hash is carried as an authorization/commit token that the forwarding layer must match. It is a finalization/audit field.

Therefore the precise finding is:

> cMCP has a pre-forwarding, privacy-preserving argument digest, but the digest is not demonstrated to be an enforceable commit binding.

## Next

T13 should test **argument mutation after hash creation** at the implementation seam.

The experiment must distinguish:
1. mutation of the original Python object after hash creation;
2. mutation of the object passed to forwarding;
3. mutation of the serialized wire payload immediately before transport.

The objective is to establish whether the existing implementation guarantees:

`hashed_arguments == forwarded_arguments`

or merely records the arguments as they existed at two separate points in the call.
