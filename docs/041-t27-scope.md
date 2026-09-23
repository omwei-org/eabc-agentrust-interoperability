# T27 — Reproducible EABC–cMCP Interoperability

T27 validates reproducibility of the frozen T26 experimental interoperability profile. It does not redefine the profile or upgrade native cMCP conformance.

## Scope

T27 covers deterministic interoperability vectors, failure preservation, repeated execution, machine-checkable provenance, explicit native-conformance boundaries, a content-addressed reproduction manifest, and reproduction against the pinned cMCP revision.

## Success condition

Declared vectors produce stable results from fresh adapter state; evidence inputs are pinned; and the generated manifest binds the exact repository bytes used by CI.

## Non-goals

Physical isolation, hardware enforcement, privileged-bypass resistance, physical-world safety, and native cMCP conformance.