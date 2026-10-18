# Runtime protocol — GEN-01 through GEN-04

Date: 2026-10-17  
Status: **PLAN ONLY — NOT EXECUTED**

## Preconditions
Run only in an isolated disposable lab against a pinned OpenShell build. Use synthetic, non-reusable credentials, harmless payloads, and a controlled canary upstream. Never use production credentials or customer data.

Required: exact source/build/runtime versions; valid policy fixtures and hashes; deterministic barriers at the intended code seams; a client transcript; proxy/OPA logs with secrets redacted; and an independent canary that records connection time, path, body hash/length, and only a boolean indicating whether the synthetic credential was present. Never log the credential value.

If a barrier cannot be placed at the intended seam, classify the scenario as INCONCLUSIVE rather than approximating with sleeps.

## Policy fixtures
- **P0 — inspected-only:** credentialed endpoint requires L7 inspection; uninspected credential traffic is not allowed.
- **P1 — explicit exception:** only for testing the documented `allow_uninspected_credentials: true` exception, scoped to the exact test endpoint.
- **P2 — quarantine:** test endpoint denied.
- **P3 — overlap:** L4-only credentialed and inspected endpoint definitions match the same host/port and have distinguishable harmless metadata.

Use the pinned version's actual supported schema. Archive effective parsed policies and hashes. If a fixture cannot be expressed, record the limitation and mark affected tests INCONCLUSIVE.

## Procedure
1. Start the canary and verify its log is empty.
2. Load initial policy; record hash and generation.
3. Start the client and pause at the deterministic barrier.
4. Publish the next policy and confirm the new generation is active.
5. Release the barrier; capture client result and relay-close behavior.
6. Collect generation snapshots, OPA/proxy traces, client transcript, and independent canary records.
7. Repeat deterministic interleavings where practical. Repetition supplements, but does not replace, barrier control.

## GEN-01 — L4 authorization vs credential guard
Place a barrier after the primary L4 decision and before the credential-guard query; add a second barrier after the query if possible. Test both P1 → P0 and P0 → P1. Record decision generation, guard query start/end, current generation, and endpoint identity.
**Expected:** setup is evaluated consistently under a valid pinned generation or rejected as stale. P1 → P0 must not deliver protected data or synthetic credentials under stale permission. The explicit exception must remain confined to the configured endpoint.

## GEN-02 — final generation check vs CONNECT success
Place a barrier immediately after the final generation/staleness check and before CONNECT success or relay startup is committed; verify the exact seam for the pinned commit. Publish P0 or P2 while paused, confirm activation, then release.
**Expected:** stale CONNECT is rejected/closed according to the implementation contract. The canary receives no protected request or credential that the new policy denies. Record upstream TCP connection separately from accepted application bytes.

## GEN-03 — active relay invalidation
Establish raw CONNECT, inspected HTTP/L7, and long-lived relay types supported by the pinned build. Publish P2 while idle, during a harmless in-flight request, and before a subsequent protected request. Record publication and close timestamps.
**Expected:** stale relay closes or becomes unusable at the documented invalidation point; the canary accepts no later protected request or synthetic credential. Distinguish pre-publication bytes from post-publication bytes; do not claim retroactive prevention.

## GEN-04 — metadata materialization sequence
Place barriers at each available seam: (1) L4 authorization, (2) L7 route, (3) credential guard, (4) TLS mode, (5) destination constraints including allowed IPs/exact-host signals, (6) final generation check, and (7) route hydration/relay startup. Reload at each boundary. Include P3 overlapping endpoints. Test absent/malformed metadata and authoritative OPA errors as separate cases.
**Expected:** metadata influencing one authorization is consistent with its claimed generation, or the operation fails closed before forbidden protected bytes/credentials arrive. Endpoint precedence is deterministic. Missing/malformed metadata does not silently broaden access.

## Result classification
- **PASS:** barrier and policy-generation transition are evidenced; behavior meets the safe expectation; the independent canary confirms no forbidden protected request/credential arrived.
- **FAIL:** the canary receives data/credentials denied by the active policy, stale CONNECT succeeds contrary to contract, or a stale relay continues protected activity beyond the required invalidation point.
- **INCONCLUSIVE:** barrier ordering or generation activation is unproven, logs are missing, or effect-side observation cannot distinguish pre- from post-reload traffic.

A proxy denial log, unit test, or source inspection alone cannot earn PASS for an upstream-receipt claim.

## Evidence manifest
For each run record scenario/run ID; source commit and build digest; platform/driver/runtime versions; policy hashes and generation values; barrier reach/release times; policy-publication acknowledgement; redacted OPA/proxy traces; client transcript; canary record with body hash/length and synthetic-credential-present boolean; relay-close timestamp; result, scope, deviations and reviewer. Never store raw credentials or reusable tokens.

## Scope
Results apply only to the pinned build, driver and fixtures. A PASS does not establish behavior for every version or policy combination. A FAIL requires triage against the documented contract before assigning vulnerability severity.

**Current status:** GEN-01 through GEN-04 remain **NOT TESTED**. This document is a protocol only; no runtime execution is claimed.