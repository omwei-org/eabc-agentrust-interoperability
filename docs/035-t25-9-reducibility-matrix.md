# T25.9 — EABC ↔ cMCP Reducibility Matrix

## Status

**Baseline matrix completed after T25.2–T25.8**

Upstream under test: public cMCP `v0.5.0`

## Classification

- **NATIVE** — behavior exists in unmodified cMCP and was observed/verified.
- **ADAPTER-DEMONSTRATED** — behavior was demonstrated by the EABC interoperability adapter at a real cMCP execution seam.
- **PARTIAL** — cMCP provides relevant primitives, but not the complete EABC semantics.
- **ABSENT** — no corresponding mechanism was identified in the tested scope.
- **NOT CLAIMED** — outside the demonstrated scope.

## Matrix

| EABC stage / property | cMCP v0.5.0 evidence | Classification |
|---|---|---|
| AO — authority object formation | authenticated MCP call/principal/context exist, but no EABC authority object | PARTIAL |
| AEE — authorization/evaluation | Cedar policy evaluation | NATIVE / scoped |
| ECT — execution context tuple | request, call_id, tool, policy context exist | PARTIAL |
| PREPARE | request hashing and call finalization setup precede forwarding | NATIVE / partial |
| FINAL_AUTHORITY_CHECK | Cedar + gateway/DLP enforcement chain | PARTIAL |
| COMMIT GATE | enforcing forwarding seam can be gated by adapter | ADAPTER-DEMONSTRATED |
| Exact execution binding | call_id + tool + request hash can be checked at forwarding | ADAPTER-DEMONSTRATED |
| Replay resistance | one adapter COMMIT rejected on second call | ADAPTER-DEMONSTRATED |
| Failure semantics | PRE_TRANSPORT vs TRANSPORT_MAY_HAVE_STARTED states | NATIVE / compatible |
| EAtt / commit evidence | terminal audit exists, but no native EABC commit_id | PARTIAL |
| COMMIT → terminal audit binding | deterministic adapter evidence object | ADAPTER-DEMONSTRATED |
| Exclusive mediation | cMCP gateway scopes MCP forwarding, not universal effects | PARTIAL / scope-bounded |
| Universal effect mediation | no evidence for arbitrary downstream effects | ABSENT / NOT CLAIMED |
| Hardware enforcement | TEE attestation exists, but physical execution boundary is outside tested seam | NOT CLAIMED |

## Key result

The experiment supports the following precise statement:

> **cMCP v0.5.0 is substantially reducible to an EABC execution-boundary profile for the MCP forwarding domain when an interoperability adapter supplies the missing exact-commit binding and commit gate. It is not demonstrated to implement the complete EABC contract natively.**

## Native versus adapter boundary

The strongest native cMCP primitives observed are:

- Cedar authorization;
- request payload hashing;
- call identity;
- execution finalization state;
- gateway enforcement;
- hash-chained terminal audit;
- explicit transport boundary states.

The adapter supplies:

- EABC COMMIT identity;
- exact COMMIT-to-call binding;
- substitution rejection;
- replay rejection;
- explicit durable COMMIT-to-terminal-audit binding.

## Remaining gaps

The experiment does not establish:

1. an independently authoritative EABC authority object;
2. native atomic EABC COMMIT semantics in unmodified cMCP;
3. native persistence of EABC `commit_id`;
4. universal/exclusive mediation over all possible effect paths;
5. hardware/physical enforcement of the downstream effect;
6. proof that terminal audit evidence establishes physical-world truth.

## Evidence chain

T25.2 → real cMCP forwarding seam  
T25.3 → terminal audit reconstruction / native absence of commit_id  
T25.4 → failure-state semantics  
T25.5 → replay resistance  
T25.6 → exact execution-object substitution resistance  
T25.7 → durable cross-layer evidence binding  
T25.8 → explicit native/adapter separation

## Overall classification

**REFINE / PROFILE CANDIDATE**

The appropriate next artifact is an explicit **EABC Profile for MCP/cMCP**, derived from this tested mapping rather than claiming full native EABC implementation.
