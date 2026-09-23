# T26.5 — Reproducible Evidence Bundle

The T26 profile result is now represented as a machine-readable evidence bundle.

Bundle:

`evidence/t26-5-conformance-bundle.json`

The bundle identifies:

- EABC-MCP profile and version;
- upstream cMCP version;
- adapter package;
- every profile MUST requirement;
- evidence test references;
- experimental conformance status;
- explicit non-claim of native cMCP conformance.

The verifier hashes the canonical JSON representation with SHA-256 and verifies that every MUST requirement has evidence.

## Verification model

`bundle → canonical serialization → SHA-256 → independent verification`

The verifier does not execute the conformance tests and does not infer missing claims.

## Status

**EXPERIMENTAL PASS**

Native cMCP EABC conformance remains **NOT CLAIMED**.
