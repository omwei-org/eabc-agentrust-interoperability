# T30.2 — Runtime forwarding admission harness

## Purpose

T30.2 defines the first runtime-shaped experiment for the proposed EABC/cMCP seam. It uses a local forwarding function as the consequence sink and makes the admission decision explicit immediately before that sink.

This remains an interoperability harness. It does not patch or modify cMCP itself and does not claim native EABC support.

## Runtime contract

request -> identity/execution binding -> authorization result -> EABC COMMIT validation -> existing forwarding callable -> upstream consequence

The forwarding callable is intentionally injected as a dependency so the test can observe whether the consequence was reached.

## Required cases

- missing commit: consequence count remains zero;
- exact commit: consequence count becomes one;
- substituted execution_id: consequence count remains zero;
- substituted request: consequence count remains zero;
- replay after terminal outcome: consequence count remains zero;
- outcome_unknown: consequence count remains zero and is not replay permission.

## Boundary

The experiment establishes the semantics of a single controlled forwarding transition. It does not establish that all production cMCP ingress paths use that transition.

The next step is to replace the injected forwarding callable with the actual cMCP runtime seam in a fork/patch experiment, then enumerate alternative production-reachable paths to the same upstream consequence.
