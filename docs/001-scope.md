# 001 — Scope

## Research question

Can an open AgenTrust component be reduced to an implementation of the EABC execution-boundary contract for a defined execution domain?

The first domain is MCP tool execution through cMCP.

## Hypothesis

cMCP may provide a concrete, hardware-attestable enforcement boundary for MCP tool calls. That does not by itself establish the complete EABC contract.

The experiment therefore separates:

1. authorization;
2. preparation;
3. final authority checking;
4. commit/forwarding;
5. exact execution binding;
6. execution evidence;
7. downstream effect;
8. mediation scope.

## Scope boundary

A result is always qualified by the execution domain tested.

For example:

> COMMIT GATE = demonstrated for cMCP forwarding

is not equivalent to:

> COMMIT GATE = demonstrated for every downstream physical effect.

## Evidence classes

### D — Documented
Claim supported by upstream documentation.

### I — Implemented
Claim supported by source inspection at a pinned upstream revision.

### O — Observable
Behavior can be observed through a stable runtime/API/test interface.

### E — Experimentally demonstrated
Behavior was reproduced by this repository's test harness.

A strong conclusion should not silently upgrade D/I/O into E.

## First phase

Software-only cMCP, using the upstream developer mode.

This phase tests execution semantics and mediation behavior. It does not establish TEE or hardware assurance.

## Later phases

Where infrastructure permits:

- TPM-backed verification
- SEV-SNP / TDX
- exact attestation evidence binding
- hardware-specific failure behavior

These remain separate experiments.
