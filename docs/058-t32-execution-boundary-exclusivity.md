# T32 — Execution-Boundary Exclusivity

T32 tests whether a production-reachable cMCP tools/call request can reach the declared forwarding consequence without satisfying the EABC execution-admission contract.

Profiles: OPTIONAL (execution-correlated requests require EABC; non-correlated requests retain legacy forwarding) and MANDATORY (all tool calls require EABC admission).

Matrix: A valid commit -> 1 forwarding / 1 effect; B missing commit -> 0 / 0; C substituted or replayed commit -> 0 / 0; D no execution_id -> 1 / 1 in OPTIONAL and 0 / 0 in MANDATORY.

The decisive observable is forwarding_entry_count, not effect count alone.

T31 = common seam. T32 = exclusivity under selected policy. This is experimental and does not claim native cMCP conformance, physical isolation, privileged-bypass resistance, physical-world effect, or distributed exactly-once execution.
