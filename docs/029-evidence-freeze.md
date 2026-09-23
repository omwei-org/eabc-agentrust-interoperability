# 029 — Evidence Freeze

## Freeze point

T24 freezes the interoperability experiment before external collaboration.

The upstream cMCP reference is pinned to:

agentrust-io/cmcp @ f8743e013786b094caaa70c336519834e73c74d5

## Three evidence classes

### 1. VERIFIED UPSTREAM

Facts observed directly in the pinned cMCP source:

- concrete CMCPProxy forwarding seam;
- real call_tool execution path;
- request handling before forwarding;
- explicit rejection of caller-supplied execution correlation;
- existing authorization, gateway and audit/evidence mechanisms.

### 2. DEMONSTRATED BY OUR ADAPTER

Properties demonstrated by the local interoperability harness:

- commit gates forwarding;
- missing commit produces no effect;
- exact request digest is enforced;
- call identity and tool identity can be bound;
- policy identity can be bound;
- commit can be correlated with cMCP call/evidence identifiers.

### 3. NOT YET DEMONSTRATED

The repository does not claim:

- unmodified cMCP implements EABC;
- atomic commit-to-audit persistence exists;
- universal/exclusive mediation over all downstream effect paths;
- physical hardware enforcement by the adapter.

## Freeze decision

The experiment is sufficiently concrete to move from technical exploration to collaboration design.

Further work should only be added when it answers a specific interoperability question or produces new evidence. It should not expand the claim beyond the frozen evidence classes.
