# T30.1 — Experimental cMCP adapter integration

## Purpose

T30.1 is a proof-of-concept integration harness against cMCP commit `f8743e013786b094caaa70c336519834e73c74d5`.

It does not modify the upstream cMCP repository and does not claim native EABC support. The harness demonstrates the smallest possible adapter point: EABC admission is evaluated immediately before the existing forwarding operation.

## Contract

The adapter receives the cMCP request tuple: agent_identity, execution_id, call_id, tool_name, arguments, policy_id.

It validates the corresponding EABC COMMIT and only then permits the modeled forwarding operation.

The harness deliberately keeps the upstream forwarding function unchanged.

## Negative cases

The integration must refuse missing EABC COMMIT, substituted execution_id, substituted request/action, replay after terminal outcome, and replay after outcome_unknown.

## Bypass test

A bypass is interesting only when an ingress reachable through the normal runtime can cause the same declared consequence without passing the EABC admission check.

Directly invoking a private forwarding method from a test is not such a bypass.

## Evidence boundary

This harness proves only adapter behavior at the proposed seam. It does not prove complete mediation of every cMCP ingress, hardware isolation, exactly once external execution, or physical effect.
