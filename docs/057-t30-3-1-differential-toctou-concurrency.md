# T30.3.1 — Differential TOCTOU and concurrency experiment

## Purpose

T30.3.1 separates three claims that must not be conflated:

1. native cMCP behavior at the pinned revision;
2. behavior of the repository-added EABC admission hook;
3. behavior under genuine concurrent calls sharing one execution identity.

The experiment therefore records baseline/control behavior rather than treating a successful hook run as evidence about native cMCP.

## Native baseline

The native pinned revision is f8743e013786b094caaa70c336519834e73c74d5.

At that revision, a supplied valid execution_id is fail-closed as execution_correlation_unavailable before upstream invocation. This is a native runtime observation. It is not evidence of an EABC gate.

The baseline is consequently documented as native refusal, not as a claimed TOCTOU vulnerability.

## Experimental control

For a forwarding comparison, the experiment may deliberately neutralize the pinned revision's execution_correlation_unavailable refusal in the disposable checkout. This is an experimental control, not native cMCP behavior.

The control must be labeled separately from the native baseline.

## Cases

Each case is evaluated with the same execution tuple and observable local MCP sink where forwarding is enabled:

1. valid admission → one observable effect;
2. authority invalidated between initial admission and final transition → no effect;
3. argument substitution → no effect;
4. replay of the same commit → no second effect;
5. two concurrent call_tool() requests sharing the same execution_id and commit → at most one observable effect.

Case 5 uses two real concurrent workers and a synchronization barrier. It does not use a sleep-based ordering assumption.

## Atomic commit consumption

The EABC adapter protects commit consumption with a lock. The check-and-consume operation is therefore one critical section for the experiment's in-process concurrency model.

This demonstrates single-use behavior under the tested concurrency model. It does not prove crash-safe distributed exactly-once semantics.

## TOCTOU semantics

The revocation case places an authority mutation after initial EABC validation and before the final authority transition. The final authority callback is explicitly invoked immediately before forwarding.

This tests: initial authority/admission → mutable interval → FINAL_AUTHORITY_CHECK → forwarding.

A no-effect result demonstrates the behavior of the experimental hook under that modeled authority mutation. It does not by itself establish a native cMCP security defect.

## Observable evidence

The local upstream sink writes a canonical JSON event to a file. The evidence bundle records its SHA-256 digest together with:

- native upstream commit;
- experiment repository commit;
- execution/call identity;
- request payload hash;
- commit identity;
- scenario;
- terminal outcome;
- sink effect count and digest.

CI must publish the resulting evidence artifact and its SHA-256 manifest.

## Claim boundary

A passing T30.3.1 run can demonstrate the tested experimental EABC behavior, including single-use behavior under the stated in-process concurrency model and the defined revocation race.

It cannot demonstrate native EABC support in cMCP, universal complete mediation, hardware enforcement, distributed exactly-once execution, or proof of a physical-world effect.
