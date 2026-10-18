# OpenShell runtime validation — evidence template

## Status

**Runtime validation: NOT TESTED.**  
**EABC/SLC conformance: INCONCLUSIVE.**

This template is for a separately executed, isolated lab run. A GitHub Actions source-level regression pass is not runtime evidence and must not be copied into the results below. Do not mark any row PASS/FAIL until an actual run and effect-side observation are attached.

## Safety and scope

- Use an isolated lab, synthetic credentials, and harmless canary effects only.
- Do not target production services, real credentials, or real protected data.
- Pin the exact OpenShell commit. Baseline requested by issue #6: `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`; if testing another commit, record the reviewed reason and exact SHA.
- This record does not assume Sentry is present. If Sentry is in scope, identify exact BlueField model, Sentry software/firmware, deployment mode, config, and source/documentation revision before testing.

## Run manifest — fill before execution

| Field | Value |
| --- | --- |
| Run ID | NOT RECORDED |
| Operator | NOT RECORDED |
| Start/end UTC | NOT RECORDED |
| Host OS/kernel | NOT RECORDED |
| Hardware / driver | NOT RECORDED |
| OpenShell repository + commit | NOT RECORDED |
| OpenShell configuration hash | NOT RECORDED |
| Policy hash / generation identifier | NOT RECORDED |
| Canary endpoint / effect oracle | NOT RECORDED |
| Test harness commit | NOT RECORDED |
| Artifact hashes | NOT RECORDED |

## Result vocabulary

- `NOT TESTED`: no execution evidence exists.
- `PASS`: expected enforcement outcome observed **and** the effect-side oracle confirms the expected upstream effect/non-effect.
- `FAIL`: reproducible violation of the test's stated expectation, with evidence.
- `INCONCLUSIVE`: execution occurred but evidence is insufficient, contradictory, or the harness failed.

A supervisor log by itself is not proof that the upstream effect did not occur. A harness failure is not a security-test failure.

## Runtime matrix

| ID | Test | Required observation | EABC mapping | Status |
| --- | --- | --- | --- | --- |
| NET-01 | Per-driver direct TCP/UDP and DNS attempts | Supervisor decision plus packet/effect-side evidence | NON_BYPASSABILITY(B,E); EBP assumptions | NOT TESTED |
| NET-02 | IPv6, ICMP, raw socket, alternate socket family, UNIX socket outside broker, rebinding, mixed A/AAAA | Each path enumerated; blocked/allowed outcome and effect-side evidence | NON_BYPASSABILITY(B,E); INTEGRITY_CTX(C,B,E) | NOT TESTED |
| GEN-01 | Stale policy generation, synchronized with a barrier | Reject decision and unchanged upstream canary counter | INTEGRITY_STATE(B,E); temporal EBP constraints | NOT TESTED |
| GEN-02 | Current valid generation control | Allow decision and exactly expected canary effect | INTEGRITY_STATE(B,E); INTEGRITY_CTX(C,B,E) | NOT TESTED |
| GEN-03 | Policy changes between check and relay/commit | Race outcome plus effect-side record; repeat with deterministic barrier | NON_BYPASSABILITY(B,E); temporal EBP constraints | NOT TESTED |
| EVAL-01 | Missing L7 metadata vs authoritative evaluation error | Fail-closed behavior and whether canary receives protected bytes/synthetic credential | INTEGRITY_STATE(B,E); NON_BYPASSABILITY(B,E) | NOT TESTED |
| VM-01 | Read-only/read-write share boundary | Exact reads/writes and canary effect | NON_BYPASSABILITY(B,E); INTEGRITY_CTX(C,B,E) | NOT TESTED |
| VM-02 | Outside-share canary; symlink/hardlink; `..` traversal | Target inode/path and whether outside canary changed | NON_BYPASSABILITY(B,E) | NOT TESTED |
| VM-03 | Source replacement race and already-open file descriptor | Object identity before/after and observed effect | INTEGRITY_CTX(C,B,E); temporal EBP constraints | NOT TESTED |
| VM-04 | Invalid target and forced mount failure | Explicit failure mode and absence/presence of effect | NON_BYPASSABILITY(B,E) | NOT TESTED |
| SENTRY-01 | Authorization, replay/staleness, requester compromise | Version-pinned policy decision and hardware/effect-side record | NON_BYPASSABILITY(B,E); INTEGRITY_STATE(B,E) | NOT TESTED |
| SENTRY-02 | Reset/downgrade and fail-closed behavior | State across reset/downgrade and effect-side record | INTEGRITY_STATE(B,E); EXCLUSIVITY | NOT TESTED |
| COMP-01 | Integrated OpenShell + Sentry protected path | Full path enumeration, decisions, and effect-side record | NON_BYPASSABILITY(B,E); EXCLUSIVITY | NOT TESTED |
| COMP-02 | Integrated failure, policy-change, and downgrade cases | Failure injection, state transition, and effect-side record | INTEGRITY_STATE(B,E); INTEGRITY_CTX(C,B,E); EBP constraints | NOT TESTED |

## Per-test evidence record

Copy this section for every executed row.

- Test ID:
- Exact command/script and version:
- Preconditions and expected result:
- OpenShell/Sentry commit and versions:
- Configuration/policy hashes:
- Start/end UTC:
- Supervisor decision/log reference:
- Network/host trace reference (if relevant):
- Canary/effect-side record before and after:
- Exit code and harness health:
- Raw artifact filenames and SHA-256:
- Actual observation:
- Result: `PASS` / `FAIL` / `INCONCLUSIVE`
- Limitations and deviations:
- EABC property mapping:
- EBP assurance constraints assessed separately:

## Evaluation guardrails

1. Keep source-level regression outcomes separate from runtime outcomes.
2. Do not mark GEN/REV/CTL rows PASS based solely on the three targeted source tests in Run #12.
3. An alternate-path attempt is a demonstrated bypass only if the same protected effect is observed without satisfying the required boundary conditions.
4. Failure to reproduce a bypass is not proof that every path is mediated; list the paths and coverage limits.
5. Sentry claims require a pinned device, firmware/software version, configuration, and enumerated commit paths.
6. Keep EABC semantic properties separate from EBP assurance constraints such as enforcement independence and timing/TOCTOU.
7. Overall EABC/SLC conformance remains INCONCLUSIVE until the concrete SLC implementation, substrate, configuration, deployment assumptions, and required evidence are assessed.
