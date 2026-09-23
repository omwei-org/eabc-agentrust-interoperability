# 011 — T07 Authority Epoch / TOCTOU Audit

## Question

Can a cMCP authorization obtained at time T1 be invalidated by an authority change at T2 before the upstream invocation at T3, using an explicit authority epoch?

## Observed cMCP behavior

The v0.5.0 execution-correlation path rejects a supplied execution ID when execution correlation is unavailable, before catalog lookup, upstream drift discovery, or forwarding. The upstream test suite therefore demonstrates a real fail-closed gate on execution correlation.

However, the audited call path does **not** expose an authority-epoch snapshot/revocation primitive comparable to the EABC Run-002 model:

`PREPARE(epoch=1) → REVOKE(epoch=2) → COMMIT → STALE_EPOCH`

A search of the v0.5.0 source baseline did not identify an `authority_epoch` mechanism.

## T07 classification

| Property | Result |
|---|---|
| authorization gate exists | DEMONSTRATED |
| execution-correlation gate exists | DEMONSTRATED |
| fail closed before forwarding | DEMONSTRATED |
| explicit authority epoch | NOT DEMONSTRATED |
| authority snapshot at prepare | NOT DEMONSTRATED |
| revocation between authorization and forwarding | NOT DEMONSTRATED |
| commit-time epoch recheck | NOT DEMONSTRATED |
| EABC-style STALE_EPOCH outcome | NOT DEMONSTRATED |

## Important distinction

This is **not** evidence that cMCP is vulnerable to a TOCTOU race.

It is evidence that the EABC authority-epoch experiment cannot currently be reproduced from the documented/exposed cMCP v0.5.0 execution path.

The correct classification is therefore **NOT DEMONSTRATED**, not FAIL.

## Why this matters

cMCP already has a genuine enforcement boundary: tool calls are intercepted, evaluated by Cedar, and enforcing mode prevents denied calls from being forwarded. citeturn0search4turn0search5

The unresolved EABC question is narrower:

> After an allow decision has been obtained, what independently revalidates that the same authority is still valid at the exact commit point?

The current execution-correlation mechanism answers a different question: whether the supplied execution identity can be correlated. It does not, by itself, establish a mutable authority epoch.

## Next test

T08 should examine **policy/configuration mutation** rather than invent an authority epoch that cMCP does not expose:

1. authorize request A under policy bundle H1;
2. change policy material to H2;
3. determine whether the running gateway reloads/rejects/re-evaluates before forwarding;
4. record whether the already-running decision can survive the configuration transition.

This separates configuration binding from authority-epoch semantics.
