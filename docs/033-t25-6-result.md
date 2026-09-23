# T25.6 — Commit Substitution Result

## Status

**PASS**

Experiment revision: `82530d07c36702bf8ca930c91f2b418bfc2f4454`  
CI run: `35861532790`  
Upstream: public cMCP `v0.5.0`

## Question

Can an EABC COMMIT bound to one execution object be substituted onto another call, tool, request payload, or policy identity?

## Results

| Binding component changed | Expected | Result |
|---|---|---|
| call_id | reject | PASS |
| tool_name | reject | PASS |
| request arguments / digest | reject | PASS |
| policy identity | reject | PASS |

All rejected substitutions were stopped at the disposable EABC forwarding gate and produced **zero forwarded effects**.

The audit chain remained valid after the rejected attempts.

## Interpretation

T25.6 demonstrates the required invariant at the interoperability adapter:

**A COMMIT is not transferable to a different execution tuple.**

The tested binding tuple is:

`commit_id + call_id + tool_name + request_payload_hash + policy_id`

## Scope limitation

This is an **adapter-demonstrated EABC property**, not a native cMCP claim.

The production cMCP v0.5.0 terminal AuditEntry does not contain an EABC `commit_id`. Therefore native cMCP does not, by itself, establish the cross-system relation:

`EABC commit_id → exact cMCP execution tuple`

That relation remains an interoperability-layer responsibility.

## Conclusion

**T25.6 PASS.**

The cMCP forwarding seam is capable of enforcing exact execution-object binding when an EABC adapter supplies the binding invariant. The experiment does not establish that unmodified cMCP natively provides this EABC invariant.
