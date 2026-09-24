# T29.4 — Execution-admission harness

## Status

**Implemented as a protocol-level harness. Native cMCP integration is not claimed.**

T29.4 turns the T29.2 experiment plan into executable state and negative-case
tests. It models the proposed seam:

    authenticated request
      -> execution_id / action-binding reservation
      -> cMCP authorization (modeled boundary)
      -> EABC FINAL_AUTHORITY_CHECK / COMMIT (modeled)
      -> forwarding admission
      -> upstream consequence (modeled)

The harness is deliberately independent of cMCP internals. It therefore tests
EABC protocol semantics without silently converting them into a native cMCP
conformance claim.

## Cases covered

1. No COMMIT / no reservation — admission is refused.
2. Exact COMMIT — matching reservation and execution tuple are accepted.
3. Substituted execution_id — refused before commit validation.
4. Substituted action/request — refused by exact binding validation.
5. Replay after terminal outcome — refused.
6. Replay after outcome_unknown — refused; unknown is not replay permission.
7. Conflicting reservation — one (agent_identity, execution_id) reservation
   cannot be replaced by a different immutable action binding.

## Evidence boundary

The tests establish software protocol behavior for the proposed admission
model. They do not establish that every production cMCP ingress is mediated
by this gate.

The next decisive step remains a real integration against the later cMCP
execution-correlation revision, including enumeration of production-reachable
paths to the declared consequence:

MCP request reaches the configured upstream MCP server.

Only that integration can test whether the forwarding boundary is actually
complete mediation for the declared effect domain.
