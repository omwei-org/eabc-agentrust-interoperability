# 003 — Test Model

## Core invariant

The central experimental question is:

> **Does the exact authorized execution request become the exact committed request and the exact executed request?**

Conceptually:

authorized_request == committed_request == executed_request

The implementation may use different representations; the test must establish the binding between them.

## Test families

### T01 — Allow → Commit → Effect

A permitted MCP request is forwarded and produces the expected mock effect.

Expected observation:

ALLOW → COMMIT_CANDIDATE → EFFECT

### T02 — Deny → No Effect

A denied request must not reach the upstream MCP server.

Expected observation:

DENY → NO_FORWARD → NO_EFFECT

### T03 — Revoke/change before commit

Change the authority or policy state after preparation but before the final execution transition.

Question:

Does the system re-evaluate the current authority at the relevant commit point?

### T04 — Request substitution

Prepare/authorize request A and attempt to forward request B.

Question:

Can the execution object change after authorization?

Expected EABC property:

A_authorized != B_executed → DENY

### T05 — Replay

Replay an otherwise valid request under a changed session, policy, epoch, or other freshness context.

Question:

What replay semantics are actually enforced?

### T06 — Direct bypass

Send the same tool request directly to the upstream MCP server rather than through cMCP.

Question:

Is cMCP the exclusive mediation path for the tested topology?

A bypass result is a mediation-scope finding, not automatically a TOCTOU finding.

### T07 — Evidence binding

Compare the request and decision represented in runtime evidence with the exact request observed at the execution boundary.

Question:

Does evidence bind the decision to the exact execution object?

### T08 — Failure semantics

Inject or induce denial, stale context, malformed request, upstream failure, or interrupted execution where practical.

Question:

Are refusal/failure states explicit and is an effect prevented where the contract requires it?

## Evidence record

Each future test result should record at minimum:

- test ID
- cMCP upstream tag/commit
- experiment repo commit
- configuration hash
- policy hash where applicable
- request digest
- decision
- commit candidate/event
- effect observation
- evidence digest
- timestamp
- result classification
- limitations

## Test integrity

The harness must not modify cMCP source for the baseline tests.

Any adapter or instrumentation added by this repository must be clearly separated from the upstream implementation and identified in the evidence.
