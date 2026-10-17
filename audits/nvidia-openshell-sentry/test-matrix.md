# Runtime test matrix — OpenShell / Sentry

This is a test plan, not a test report. All rows begin **NOT TESTED** until an execution record is added. Run only in an isolated lab with synthetic credentials and harmless canary data.

| ID | Target | Test | Expected fail-closed / safe result | Evidence to capture | Status |
|---|---|---|---|---|---|
| NET-01 | Docker | Direct TCP to public IP without configured relay | No direct egress | Exact image/commit, command, packet capture, broker logs | NOT TESTED |
| NET-02 | Docker / Podman / VM separately | Direct UDP, DNS, alternate socket family and socket rebind attempts | Unsupported or unauthorized path rejected | Per-driver results and syscall/network traces | NOT TESTED |
| NET-03 | Each driver | Kill/restart supervisor or broker while a connection is attempted | No fail-open direct path | Failure timing, logs, packet capture | NOT TESTED |
| NET-04 | Each driver | Private, link-local, metadata IPs; DNS rebinding and mixed A/AAAA answers | Denied unless explicitly authorized by policy | Resolver answers, decision logs, upstream canary logs | NOT TESTED |
| CRED-01 | Docker E2E | Wrong host/port/path, alias, untrusted CA, disallowed binary | Backend sees no accepted protected call | Backend counters, request trace, test output | NOT TESTED |
| CRED-02 | Docker E2E | Rotate provider credential A→B; compare persistent and ordinary references; revoke A | Persistent reference uses current B; revoked ordinary reference rejected | Provider state, counters, output | NOT TESTED |
| GEN-01 | Supervisor proxy | Reload policy between main authorization and credential-guard query | Stale decision rejected before upstream protected bytes | Barrier timestamps, generation IDs, upstream capture | NOT TESTED |
| GEN-02 | Supervisor proxy | Reload between final generation check and CONNECT 200 | Stale CONNECT rejected or immediately closed before protected bytes | Proxy logs, client transcript, upstream capture | NOT TESTED |
| GEN-03 | Active relay | Publish fail-closed generation during raw/HTTP relay | Stale relay closes promptly | Generation timeline, socket traces, bytes transferred after reload | NOT TESTED |
| EVAL-01 | OPA/proxy | Compare absent L7 metadata with authoritative evaluation error | Only documented missing-metadata compatibility case may use fallback; evaluation error denies | OPA inputs/results and proxy decisions | NOT TESTED |
| VM-01 | VM/libkrun | RO and RW virtiofs behavior with temporary share | RO cannot mutate host share; RW changes only intended share | Host hashes, guest commands, logs, versions | NOT TESTED |
| VM-02 | VM/libkrun | Put harmless canary file outside allowed share on same filesystem; attempt access from guest | Guest cannot access outside share due to effective host isolation | Host mount namespace/process config, guest output, audit logs | NOT TESTED |
| VM-03 | VM/libkrun | Symlink final component, symlink parent component, replace source during provisioning | Invalid path rejected; no unintended host path exposed | Race script, filesystem layout, logs | NOT TESTED |
| VM-04 | VM/libkrun | Attempt reserved/overlapping guest targets and force virtiofs mount failure | Provision/mount fails rather than silently continuing without intended semantics | Manifest, init logs, guest mount table | NOT TESTED |
| SENTRY-01 | Sentry standalone | Identify exact protected effect and enumerate every commit path, including alternate/local paths | Every path to protected effect passes the claimed enforcement boundary | Versioned architecture, wiring, bypass attempts | NOT TESTED |
| SENTRY-02 | Sentry standalone | Compromise/disable requester software; attempt replay, stale authorization, reset/downgrade and failure modes | Protected effect cannot commit without valid boundary satisfaction | Threat model, traces, hardware/config versions | NOT TESTED |
| COMP-01 | OpenShell + Sentry | Exercise authorized and denied requests end-to-end through actual integrated deployment | Only intended protected effects commit; no alternate path | Architecture, policy, component versions, traces | NOT TESTED |
| COMP-02 | OpenShell + Sentry | Fail/restart either component, change policy, downgrade configuration, disconnect control channel | Composition fails closed and preserves binding between authorization and effect | Fault injection, timing, effect-side records | NOT TESTED |

## Execution record template

For every attempted row, add:

- Date/time and operator.
- Host OS/version and hardware.
- OpenShell commit, driver, libkrun/Sentry firmware and software versions.
- Exact test command/script revision and configuration/policy hashes.
- Expected result and observed result.
- Logs, packet captures, effect-side records and artifact paths.
- Outcome: PASS / FAIL / INCONCLUSIVE; explain deviations.
- Scope limitations and whether the result applies to Docker, Podman, VM, Sentry, or their composition.

Do not mark a test PASS based only on a unit-test name or code inspection.