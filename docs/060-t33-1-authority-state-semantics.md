# T33.1 — Authority-State Semantics

## Status

**PROPOSED CONTRACT EXTENSION — NOT NATIVE cMCP CONFORMANCE**

T33.1 adds the minimum authority-state semantics required for a future native integration to reason about revocation and authority changes between authorization, execution admission, COMMIT, and forwarding.

The key property is temporal:

> Execution authority MUST be valid at the execution-boundary transition that can cause the declared consequence.

This is distinct from validating whether a commit is syntactically well-formed or whether the original authorization decision was valid when issued.

## 1. Authority state

An EABC execution-authority state is represented by a monotonically changing `authority_epoch` or equivalent version identifier.

A change that invalidates previously admitted execution authority MUST advance or otherwise distinguish the authority state.

Examples include:

- explicit revocation;
- principal disablement;
- tool-level authority withdrawal;
- policy change that invalidates the action;
- execution-domain authority transition.

The exact storage and distribution mechanism is implementation-defined.

## 2. Binding

A successful execution commit MUST carry the authority state against which its execution authority was established:

`execution_commit.authority_epoch`

The epoch is part of the execution-authority binding, not an unrelated audit field.

Conceptually:

`action_tuple + authority_epoch → execution_commit`

The action tuple remains:

`agent_identity + execution_id + call_id + tool_name + request_payload_hash + policy_id`

## 3. Temporal validation

For a strict execution-boundary profile, the forwarding transition MUST NOT accept a commit when:

`commit.authority_epoch != current_authority_epoch`

or when the authority represented by the commit has been explicitly revoked.

This check occurs at the execution boundary, immediately before the consequence-causing forwarding transition.

## 4. Atomic admission variant

A native implementation MAY implement admission as an atomic operation:

`check current authority + bind exact action + issue single-use COMMIT`

This is the preferred semantic shape when no separate PREPARE state is required.

The important property is that the authority state used to issue the COMMIT is explicit and that the commit remains subject to the declared consume semantics.

## 5. Prepare/finalize variant

Where PREPARE and FINALIZE are separate operations:

`PREPARE`
→ capture authority state
→ authority may change
→ `FINAL_AUTHORITY_CHECK`
→ issue COMMIT only if the captured state remains valid.

A stale PREPARE MUST NOT be sufficient to produce a COMMIT.

## 6. Commit/consume semantics

For the **Strict** profile:

`consume(commit) → allow`

only if all of the following hold:

- commit is single-use;
- exact action binding matches;
- commit has not expired;
- authority has not been explicitly revoked;
- current authority state matches the commit's authority state.

For an epoch mismatch or revocation:

`consume(commit) → DENY`

and the forwarding transition MUST NOT be entered.

## 7. Optional best-effort semantics

A best-effort profile MAY permit a previously issued commit to survive a subsequent authority change, but only as an explicit policy choice with a bounded validity window.

Such behavior is **not** the strict execution-boundary property tested by T34.

It MUST NOT be silently inferred from the existence of a valid commit.

## 8. Contract addition to T33

The T33 native integration contract therefore gains:

`authority_epoch`

inside the execution commit and a mandatory semantic statement for Strict mode:

> A commit is executable only while the authority state under which it was issued remains valid at the forwarding boundary.

T33.1 does not claim that upstream cMCP currently implements this field or semantic.

