# Native cMCP execution-correlation observation

- Evidence ID: T30-NATIVE-EXEC-CORR-001
- Upstream repository: agentrust-io/cmcp
- Exact upstream commit: f8743e013786b094caaa70c336519834e73c74d5
- Observation: supplied valid execution_id is refused with execution_correlation_unavailable before upstream invocation.
- Evidence tier: Implemented — native runtime behavior observed/documented at the pinned commit.
- Independence: this record does not depend on the repository-added T30.3 EABC hook.
- Not claimed: EABC conformance, TOCTOU vulnerability, complete mediation, hardware enforcement, or external-effect proof.
- Related experiment: T30.3 / T30.3.1 may use a disposable patch to compare behavior, but that does not alter this native observation.

The exact commit distinction is material: the released cMCP v0.5.0 baseline used elsewhere in this repository is d03b9af504535d3d43f192bc6d9eff89b8afd12f. This record refers specifically to the later revision f8743e013786b094caaa70c336519834e73c74d5.
