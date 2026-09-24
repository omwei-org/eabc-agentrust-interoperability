# T29.1 — cMCP Execution-Correlation Seam Analysis

## Status

**Analytical interoperability step — no native EABC conformance claim**

T29.1 resolves the revision mismatch discovered while analyzing T29 and identifies the execution-correlation seam in a later cMCP revision.

## Revision boundary

T27 and the current T26 profile are pinned to cMCP revision:

`d03b9af504535d3d43f192bc6d9eff89b8afd12f`

That revision is cMCP v0.5.0 and does not contain `execution_id` or the execution-correlation admission path.

A later cMCP revision, including commit `f8743e013786b094caaa70c336519834e73c74d5`, introduces execution correlation and action-binding machinery. This is a different revision and MUST NOT be silently treated as the T27/v0.5.0 implementation.

## What the later cMCP seam provides

The later revision introduces:

```
execution_id
    ↓
execution action binding
    ↓
execution admission / correlation
    ↓
call terminal + audit binding
```

The implementation currently refuses a supplied execution correlation identifier with `execution_correlation_unavailable` until the associated action-binding, persistence, crash/recovery, and replay contracts are implemented.

Therefore:

**execution_id is not an execution authorization grant and is not an EABC COMMIT.**

It is a correlation/admission identity whose semantics are deliberately separated from external-effect truth.

## Relevant architectural seam

The later call path is structurally compatible with an EABC integration point:

```
public MCP tools/call
        ↓
CMCPProxy.call_tool()
        ↓
execution admission / cMCP authorization
        ↓
[EABC FINAL_AUTHORITY_CHECK]
        ↓
[EABC COMMIT]
        ↓
_forward_to_upstream()
        ↓
upstream MCP consequence
        ↓
terminal audit / evidence
```

The bracketed stage is the interoperability hypothesis, not an existing native cMCP feature.

## Relation to cMCP embodied-action evidence

cMCP's embodied-action profile already separates:

- cMCP audit entry: what the gateway decided and forwarded;
- evidence envelope: binding an external issuer assertion to `call_id`;
- detached action evidence: action semantics and optional downstream receipt.

It explicitly states that such evidence does not itself prove that a physical action occurred. This aligns with the EABC distinction between evidence of execution and proof of external effect.

## T29 implication

The next test should not be another direct invocation of the private forwarding method.

The meaningful experiment is:

1. construct one exact execution object;
2. establish cMCP authorization and execution-correlation identity;
3. perform an explicit EABC FINAL_AUTHORITY_CHECK;
4. issue exactly one EABC COMMIT bound to that object;
5. invoke the existing upstream forwarding seam;
6. preserve terminal state and evidence;
7. attempt substitution and replay;
8. verify that no production-reachable alternative ingress can cause the same declared MCP-forwarding consequence without the commit.

## Claim boundary

If this experiment succeeds, the result is an **EABC interoperability profile at the cMCP execution-admission/forwarding seam**.

It does not establish:

- native cMCP EABC conformance;
- hardware-enforced EABC semantics;
- universal mediation outside the declared MCP-forwarding effect domain;
- physical-world execution authority;
- proof that a physical effect occurred.

The key question remains:

> For the declared MCP-forwarding effect domain, is COMMIT the exclusive controlled transition into the consequence?

## Collaboration interpretation

This leaves the roles cleanly separated:

- **AgenTrust/cMCP:** authenticated identity, TEE attestation, Cedar authorization, policy/configuration identity, execution correlation, audit and TRACE evidence.
- **EABC:** independent execution authority, exact commit binding, final authority check, commit semantics, single-use/replay semantics, and the exclusive mediation claim scoped to the declared consequence boundary.

The proposed interoperability experiment therefore extends cMCP rather than replacing its policy or attestation architecture.
