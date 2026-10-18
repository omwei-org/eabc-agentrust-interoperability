# Sentry integration target — public-source inventory

## Status

**Target identification: PARTIAL. Runtime target pin: NOT READY.**  
**Sentry runtime tests: NOT TESTED.**

This record distinguishes public architecture claims from a reproducible implementation target. A product announcement is not a versioned Sentry test artifact.

## Publicly stated architecture

The NVIDIA Open Agent Safety Platform announcement and NVIDIA developer material describe:

- OpenShell as the software runtime/sandbox boundary.
- NVIDIA Sentry as an additional out-of-band enforcement/monitoring layer associated with NVIDIA BlueField-4 DPUs.
- NVIDIA DOCA as the programmable software foundation used by Sentry.
- The intended architecture as an independent layer outside the agent/host execution domain.

Sources checked 2026-10-18:

1. NVIDIA Developer Blog, “NVIDIA Open Agent Safety Platform: A Reference for Continuous In-Silicon Agent Monitoring,” published 2026-09-28: https://developer.nvidia.com/blog/nvidia-open-agent-safety-platform-a-reference-for-continuous-in-silicon-agent-monitoring/
2. NVIDIA Open Agent Safety Platform overview: https://www.nvidia.com/en-gb/solutions/ai/agent-safety/
3. NVIDIA press release, 2026-09-28: https://nvidianews.nvidia.com/news/open-agent-safety-platform

These sources support identifying **BlueField-4 + NVIDIA Sentry + DOCA** as the announced reference architecture. They do not, by themselves, identify a reproducible Sentry software/firmware release or expose a complete commit-path implementation for independent testing.

## Required before SENTRY-01/02 or COMP-01/02

| Required field | Current evidence | Status |
| --- | --- | --- |
| BlueField hardware model/SKU and revision | Public material names BlueField-4; no physical lab device recorded | GAP |
| BlueField firmware/BSP version | No version pinned in the sources above | GAP |
| DOCA release and package versions | DOCA named; exact release/package set not pinned | GAP |
| Sentry software/source revision | Public reference-design descriptions; no exact source SHA pinned here | GAP |
| Sentry deployment mode and topology | General out-of-band architecture described; lab topology not recorded | GAP |
| Policy/configuration hashes | No lab configuration recorded | GAP |
| Protected effect and commit-path inventory | No concrete lab target/effect recorded | GAP |
| Independent effect-side oracle | Not configured or run | GAP |
| Reset/downgrade procedure and recovery evidence | Not documented for a pinned target | GAP |

## Decision

Do **not** mark SENTRY-01, SENTRY-02, COMP-01, or COMP-02 as PASS or FAIL. They remain **NOT TESTED** until a specific supported hardware/software target and lab setup are available and recorded.

The next Sentry-specific action is target acquisition/identification, not a simulated test result:
1. Obtain the exact BlueField-4 device/SKU and firmware/BSP information from the intended lab.
2. Obtain the supported DOCA release and Sentry software/source revision plus its configuration/deployment documentation.
3. Identify every path that can commit the protected effect, including any host-side or alternate network path.
4. Define a harmless canary effect and an independent effect-side observation.
5. Pin all versions and hashes before running authorization, replay/staleness, reset/downgrade, and fail-closed tests.

## EABC/EBP boundary

The intended independent hardware layer is an architectural claim, not proof of `ENFORCEMENT_INDEPENDENCE` for a concrete deployment. Assess that EBP assurance constraint separately from EABC semantic properties. Do not infer `NON_BYPASSABILITY(B,E)`, `INTEGRITY_STATE(B,E)`, or `EXCLUSIVITY` from the product description alone.
