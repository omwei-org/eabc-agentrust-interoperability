# 027 — T22 Result

## Scope

T22 implements the complete semantic sequence in a test harness:

call_tool → EABC commit gate → forwarding seam → effect.

It uses the same correlation vocabulary established in T21.

## Observed result

The positive path produces exactly one effect after a valid commit.

The negative paths produce zero effects for:

- no commit;
- mismatched call_id;
- mismatched request digest.

The forwarding seam receives the exact canonical argument set represented by the commit digest.

## Interpretation

T22 demonstrates the intended execution-boundary semantics at the integration seam.

It is still a harness result, not a claim about unmodified cMCP production behavior.

The remaining engineering step is to run this gate against the actual cMCP call_tool implementation and its mock upstream server in CI.

## Collaboration conclusion

The technical hypothesis is now sufficiently concrete for an AgenTrust-facing experiment:

**Existing cMCP authorization and evidence can remain intact while an explicit EABC commit relation is introduced at the forwarding seam and correlated to cMCP call/evidence identifiers.**

The next artifact should therefore be a short collaboration proposal, accompanied by the reproducible test repository and a clear separation between:

- verified cMCP behavior;
- EABC profile semantics;
- adapter-level demonstration;
- proposed future integration.
