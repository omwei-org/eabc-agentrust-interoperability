# Sentry and OpenShell composition — public claims vs. EABC evidence

Date: 2026-10-17  
Scope: NVIDIA public descriptions of Sentry and the Open Agent Safety Platform, compared with the evidence needed for an EABC assessment. This is not an implementation audit or hardware validation. Public web pages were consulted on 2026-10-17; where a page is a rolling URL, the access date records the snapshot time, not a guarantee of immutable content.

## Assessment

**Sentry standalone enforcement: NOT TESTED (implementation/runtime evidence absent).**  
**OpenShell + Sentry composition: NOT TESTED (integration evidence absent).**

Official NVIDIA materials now describe Sentry as an optional, independent hardware security layer alongside OpenShell, running on BlueField-4 and using DOCA for out-of-band observation, identity governance and policy enforcement. NVIDIA describes the combined Open Agent Safety Platform as an open reference system design, not as a claim that every OpenShell deployment includes Sentry.

Sources:
- [NVIDIA Open Agent Safety Platform press release, 2026-09-28](https://nvidianews.nvidia.com/news/open-agent-safety-platform)
- [NVIDIA technical blog: reference for continuous in-silicon agent monitoring, 2026-09-28](https://developer.nvidia.com/blog/nvidia-open-agent-safety-platform-a-reference-for-continuous-in-silicon-agent-monitoring)
- [NVIDIA Open Agent Safety Platform overview and FAQ](https://www.nvidia.com/en-us/solutions/ai/agent-safety/)
- [OpenShell architecture documentation](https://docs.nvidia.com/openshell/dev/about/architecture) — rolling `dev` documentation, accessed 2026-10-17.

These materials are **vendor documentation/claims**. They are useful to define the intended trust model, but do not establish that the implementation has the described properties under a concrete deployment, nor that Sentry is EABC-conformant.

## What the public materials claim

- OpenShell enforces the software/runtime boundary: sandbox isolation, policy-controlled network access, filesystem/process controls, credential handling and a supervisor outside the agent process.
- Sentry is described as an independent, out-of-band watchdog on BlueField-4, using DOCA to observe agent activity and enforce policy in hardware.
- The combined design is described as able to quarantine/stop an agent in milliseconds when it attempts to leave its boundary.
- NVIDIA says Sentry is an optional security layer alongside OpenShell. OpenShell itself can run without BlueField-4/Sentry.

These statements are not independently verified by this audit. In particular, marketing-level phrases such as “every request and response,” “attested telemetry,” “independent,” or “quarantine in milliseconds” need a precise technical scope and observable acceptance criteria.

## Evidence required to assess Sentry by itself

1. **Protected effect and boundary:** identify the exact paths Sentry mediates (model access, APIs/tools, data access, network egress, or a stated subset), and list paths it does not cover.
2. **Identity and context binding:** show how agent identity, tenant/sandbox identity, delegated authority, policy version and workload generation are authenticated and bound to each observed/enforced request.
3. **Independent enforcement:** demonstrate that a compromised host/workload cannot disable, spoof or bypass Sentry's enforcement path or its telemetry.
4. **Fail-safe behavior:** specify and test behavior on DOCA/Sentry service failure, DPU reset, policy delivery loss, stale identity, missing telemetry, link/path failover and restart.
5. **Effect-side proof:** run denied and allowed synthetic requests through the actual supported hardware path; capture Sentry decision/telemetry and independent destination-side records. A log entry alone is not proof that the protected effect was blocked.
6. **Scope of the claim:** pin firmware, DOCA/Sentry software, BlueField model, host topology, policy and versions; state whether the result is specific to BlueField-4/Vera reference topology.

## Evidence required for OpenShell + Sentry composition

The composition must be assessed as a single boundary, not by adding together component claims.

- Define the policy source of truth and how OpenShell policy is translated, versioned, authenticated and delivered to Sentry.
- Define which layer is authoritative for each protected effect and how conflicts/updates are handled.
- Bind OpenShell sandbox/session/runtime generation and process or agent identity to Sentry's identity and telemetry context.
- Prove that every claimed path to the protected effect crosses at least one enforcing layer, including alternate NICs, host routes, alternate model endpoints, tool/API paths, recovery paths and administrative channels.
- Test policy update/revocation races, host compromise assumptions, Sentry outage/restart, stale policy and quarantine completion.
- Observe the protected effect at an independent destination and show that a forbidden request does not arrive, or that an already active path is cut within a measured bound.
- State residual trust in firmware, DPU, host BIOS/IOMMU, management plane and operator configuration.

## EABC mapping

| EABC question | Evidence needed |
|---|---|
| `INTEGRITY_DEF(B)` | Complete and versioned definition of the Sentry boundary, protected effects and excluded paths. |
| `INTEGRITY_STATE(B,E)` | Demonstrated state transitions for policy update, revocation, DPU/service failure and quarantine. |
| `INTEGRITY_CTX(C,B,E)` | Authenticated binding of agent/sandbox identity, generation, policy version and observed effect. |
| `NON_BYPASSABILITY(B,E)` | Effect-side proof that all relevant paths are mediated or denied, including alternate/failure paths. |
| `EXCLUSIVITY` | Evidence that only the intended authority can approve or perform the protected effect and that Sentry/host cannot silently expand authority. |

## Current disposition

- Public documentation supports the intended architectural role of Sentry as an optional independent hardware layer.
- No Sentry implementation source, pinned firmware/software build, deployment configuration, hardware lab output, failure-injection result or independent effect-side trace was collected for this audit.
- Therefore, neither Sentry's standalone enforcement nor the OpenShell+Sentry composition can currently receive PASS/FAIL under EABC from this evidence.
- Keep `SG-01` and `COM-01` **NOT TESTED** at implementation/runtime level. `NOT TESTED` is the test-status vocabulary; `VENDOR DOC-CLAIM only` is an evidence classification, not a second result state. Overall EABC verdict remains **INCONCLUSIVE**.

