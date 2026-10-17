# Runtime test matrix — OpenShell / Sentry

This is a test plan, not a test report. No runtime tests are represented as executed. Every row starts with status `NOT TESTED`. Run only in an isolated lab using synthetic credentials and harmless canary data.

## Result-state vocabulary

- `NOT TESTED`: no adequate runtime execution record exists.
- `INCONCLUSIVE`: test ran, but evidence does not decide the stated hypothesis.
- `PASS`: observed behavior meets the explicit expected result in the recorded scope.
- `FAIL`: observed behavior violates the explicit expected result in the recorded scope.

Do not use `NOT REPRODUCED` unless an actual reproduction attempt ran and its conditions/results are recorded. Evidence class is separate from test result: `DOC-CLAIM`, `SOURCE`, `TEST-CONTRACT`, `RUNTIME`.

## Baseline-drift gate

Before treating this matrix as applicable to current upstream `main`, review BASELINE-01 in `findings.md`. The current matrix is pinned to OpenShell `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`; current upstream was observed at `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`. Do not replace the baseline in place. Either execute this matrix against the pinned baseline, or create a separately versioned matrix and evidence record for the newer commit, after reviewing the changed isolation contract, RPC protocol, conformance tests, driver implementations and network recovery behavior.

## Test matrix

| ID | Target | Test | Expected safe result | Evidence to capture, including effect-side observation | Evidence class at planning stage | EABC criterion | Status |
|---|---|---|---|---|---|---|---|
| NET-01 | Docker | Attempt direct TCP to a controlled public canary IP without configured relay | No direct egress; canary receives no connection or payload | Exact image/commit/config, command, packet capture, broker logs, canary connection log | DOC-CLAIM + SOURCE + TEST-CONTRACT | NON_BYPASSABILITY(B,E); INTEGRITY_CTX(C,B,E) | NOT TESTED |
| NET-02 | Docker / Podman / VM separately | Try direct UDP and DNS, IPv4 and IPv6, ICMP, raw sockets, alternate socket families, socket rebinding, and UNIX socket paths outside the approved broker; include mixed A/AAAA answers | Unsupported or unauthorized paths are rejected; no unmediated path reaches canary | Per-driver command/script, syscall and network traces, resolver answers, broker logs, canary-side records | DOC-CLAIM + SOURCE + TEST-CONTRACT | NON_BYPASSABILITY(B,E); INTEGRITY_CTX(C,B,E) | NOT TESTED |
| NET-03 | Each driver | Kill/restart supervisor or broker during attempted connection and while a connection is active | No fail-open path; protected traffic stops or is denied | Fault-injection timeline, process logs, packet capture, upstream canary records | SOURCE + TEST-CONTRACT | NON_BYPASSABILITY(B,E); INTEGRITY_STATE(B,E) | NOT TESTED |
| NET-04 | Each driver | Attempt private, link-local and metadata targets; DNS rebinding and mixed A/AAAA responses | Denied unless explicitly authorized; resolved destination remains within the authorized decision | Resolver answers, policy decision/generation, packet capture, canary/upstream records | SOURCE + TEST-CONTRACT | INTEGRITY_CTX(C,B,E); NON_BYPASSABILITY(B,E) | NOT TESTED |
| CRED-01 | Docker E2E | Wrong host/port/path, alias, untrusted CA and disallowed binary against synthetic endpoint | Backend receives no accepted protected call and no injected credential | Config/policy hashes, request trace, client result, backend counters and credential-safe audit record | TEST-CONTRACT | INTEGRITY_CTX(C,B,E); EXCLUSIVITY; NON_BYPASSABILITY(B,E) | NOT TESTED |
| CRED-02 | Docker E2E | Rotate provider credential A→B; compare persistent and ordinary references; revoke A | Persistent reference uses current B as designed; revoked ordinary reference is rejected | Provider-side generation/counters, request trace and test output; never store raw secret values | TEST-CONTRACT | INTEGRITY_CTX(C,B,E); EXCLUSIVITY | NOT TESTED |
| GEN-01 | Supervisor proxy | Place a barrier between main authorization and credential-guard evaluation; reload policy from raw-tunnel allowed to L7/credential-constrained and reverse | Stale decision cannot send protected request or injected credential to upstream | Barrier timestamps, generation IDs, client transcript, proxy logs AND upstream canary logs showing whether protected bytes/credential arrived | SOURCE + TEST-CONTRACT | INTEGRITY_STATE(B,E); INTEGRITY_CTX(C,B,E); NON_BYPASSABILITY(B,E) | NOT TESTED |
| GEN-02 | Supervisor proxy | Reload policy between final generation check and CONNECT success | Stale CONNECT rejected/closed before protected bytes reach upstream | Client transcript, generation timeline, proxy logs AND upstream canary connection/payload record | SOURCE + TEST-CONTRACT | INTEGRITY_STATE(B,E); NON_BYPASSABILITY(B,E) | NOT TESTED |
| GEN-03 | Active relay | Publish fail-closed generation during raw/HTTP relay | Stale relay closes; no protected bytes or injected credential flow after the applicable invalidation point | Generation timeline, socket traces, byte counts, proxy logs AND upstream canary records | SOURCE + TEST-CONTRACT | INTEGRITY_STATE(B,E); NON_BYPASSABILITY(B,E) | NOT TESTED |
| EVAL-01 | OPA/proxy | Compare absent L7 metadata with authoritative evaluation error, including credential-injection endpoints | Authoritative evaluation error denies. Missing-metadata fallback must not weaken the applicable boundary or expose injected credentials | OPA input/result, policy and generation, proxy decision, client transcript, upstream canary record | TEST-CONTRACT + SOURCE | INTEGRITY_CTX(C,B,E); EXCLUSIVITY; NON_BYPASSABILITY(B,E) | NOT TESTED |
| VM-01 | VM/libkrun | RO and RW virtiofs behavior with temporary share | RO cannot mutate host share; RW changes only the intended share | Host hashes, guest commands, mount table, logs, host/guest versions | SOURCE + TEST-CONTRACT | INTEGRITY_DEF(B); NON_BYPASSABILITY(B,E) | NOT TESTED |
| VM-02 | VM/libkrun | Put harmless canary files outside allowed share on same filesystem; attempt access from guest | Guest cannot access paths outside the authorized share | Host mount namespace and VMM process configuration, guest output, host audit logs and canary access logs | DOC-CLAIM + SOURCE | INTEGRITY_DEF(B); NON_BYPASSABILITY(B,E); INTEGRITY_CTX(C,B,E) | NOT TESTED |
| VM-03 | VM/libkrun | Test final and parent symlinks, symlinks and hardlinks inside share pointing outside, `..` traversal, source replacement during provisioning, and already-open file descriptors | No path or descriptor grants access outside the authorized share; invalid paths/races fail safely | Exact filesystem layout, race script, inode/device identities, host and guest traces, canary access logs | SOURCE + TEST-CONTRACT | INTEGRITY_DEF(B); NON_BYPASSABILITY(B,E); INTEGRITY_CTX(C,B,E) | NOT TESTED |
| VM-04 | VM/libkrun | Attempt reserved/overlapping guest targets and force virtiofs mount failure | Provision/mount fails rather than silently continuing with unintended semantics | Manifest, init logs, guest mount table, host-side records | SOURCE + TEST-CONTRACT | INTEGRITY_DEF(B); NON_BYPASSABILITY(B,E) | NOT TESTED |

| BASELINE-02-01 | Docker / built-in backend | Compare provisioning evidence digest against actual native state; inject wrong generation, unexpected network and incomplete/malformed native evidence where test seams permit | Boundary confirmation fails before workload launch whenever native enforcement requirements are not satisfied | Driver-native state, descriptor and confirmation payloads, supervisor result, upstream canary | TEST-CONTRACT + SOURCE | NON_BYPASSABILITY(B,E); INTEGRITY_CTX(C,B,E) | NOT TESTED |
| BASELINE-02-02 | Podman / built-in backend | Test network fence, revocation and controller/broker loss | No unmanaged egress; previously allowed traffic is revoked as specified; controller loss does not open access | Host networking state, broker logs, packet capture, upstream canary | TEST-CONTRACT + SOURCE | NON_BYPASSABILITY(B,E); INTEGRITY_STATE(B,E) | NOT TESTED |
| BASELINE-02-03 | VM / built-in backend | Test VM network fence, revocation and boundary-controller failure | No unmanaged egress; controller loss fails closed; revocation matches policy | VM config, host/guest network state, packet capture, upstream canary | TEST-CONTRACT + SOURCE | NON_BYPASSABILITY(B,E); INTEGRITY_STATE(B,E) | NOT TESTED |
| BASELINE-02-04 | Delegated backend | Return null, empty, malformed and semantically incomplete audit/confirmation data; test wrong generation/session/identity/resource claims and mismatched evidence digest | Reject before agent launch unless trusted delegated validation establishes required boundary and launch binding | RPC transcript, descriptor/confirmation, driver-side native validation evidence, supervisor result, upstream canary | TEST-CONTRACT + SOURCE | INTEGRITY_DEF(B); INTEGRITY_CTX(C,B,E); NON_BYPASSABILITY(B,E) | NOT TESTED |
| SENTRY-01 | Sentry standalone | First pin exact Sentry software/firmware version, device/model, deployment mode and configuration; then identify protected effect and enumerate every commit path, including alternate/local paths | Audit scope is reproducible; every path to the protected effect traverses the claimed boundary | Version/firmware identifiers, wiring and architecture, threat model, effect-side traces and bypass attempts | NOT ASSESSED until pinned evidence is collected | To be determined from concrete boundary and protected effect | NOT TESTED |
| SENTRY-02 | Sentry standalone | With pinned version, compromise/disable requester software; test replay, stale authorization, reset/downgrade and failure modes | Protected effect cannot commit without valid boundary satisfaction | Exact versions/config, fault-injection steps, authorization/effect traces, hardware records | NOT ASSESSED until pinned evidence is collected | NON_BYPASSABILITY(B,E); INTEGRITY_STATE(B,E); INTEGRITY_CTX(C,B,E), as applicable | NOT TESTED |
| COMP-01 | OpenShell + Sentry | Pin OpenShell commit and exact Sentry software/firmware/device/config; exercise authorized and denied requests end-to-end | Only intended protected effects commit; no alternate path bypasses the composed boundary | Architecture and versions, policy/config hashes, component logs, client transcript AND protected-effect-side record | NOT ASSESSED until both components and deployment are pinned | To be determined for the composed boundary; assess NON_BYPASSABILITY(B,E) and binding of context/state | NOT TESTED |
| COMP-02 | OpenShell + Sentry | With pinned composition, fail/restart either component, change policy, downgrade configuration and disconnect control channel | Composition fails safely and preserves authorization-to-effect binding | Fault-injection timeline, versions/config, component logs, client transcript AND protected-effect-side record | NOT ASSESSED until both components and deployment are pinned | NON_BYPASSABILITY(B,E); INTEGRITY_STATE(B,E); INTEGRITY_CTX(C,B,E), as applicable | NOT TESTED |

## Execution record template

For every attempted row, add:

- Date/time and operator.
- Host OS/version, hardware, and relevant isolation settings.
- OpenShell commit, driver, libkrun version, and Sentry firmware/software/device versions where applicable.
- Exact test command/script revision and configuration/policy hashes.
- Expected result and observed result.
- Client-side result and independent upstream/protected-effect-side observation.
- Logs, packet captures, effect-side records, and artifact paths.
- Result: `PASS`, `FAIL`, or `INCONCLUSIVE`; explain deviations.
- Scope limitations and whether the result applies to Docker, Podman, VM, Sentry, or their composition.

Do not mark a test `PASS` based only on a unit-test name, code inspection, or supervisor logs when the claim concerns whether a protected effect or credential reached its destination.
