# T30 — EABC execution-admission seam proposal

## Purpose

T30 defines the smallest interoperability contract needed to place EABC execution authority at the cMCP forwarding boundary without replacing cMCP identity, Cedar authorization, TEE enforcement, audit, or TRACE.

cMCP remains the policy/enforcement runtime. EABC contributes the execution-authority decision at the declared consequence boundary.

## Proposed seam

authenticated request
  -> cMCP request / identity binding
  -> execution_id + immutable action binding
  -> cMCP Cedar authorization
  -> EABC FINAL_AUTHORITY_CHECK
  -> EABC COMMIT
  -> existing upstream forwarding
  -> cMCP audit / TRACE

The declared consequence for this profile is: the MCP request is sent to the configured upstream MCP server.

## Minimal contract

### Inputs to EABC

- authenticated agent identity;
- execution_id;
- cMCP call_id / attempt identity;
- tool_name;
- canonical request payload hash;
- applicable cMCP policy/config identity;
- immutable action binding;
- final authority snapshot/reference.

### EABC result

A successful execution admission returns an EABC COMMIT containing at minimum commit_id, the exact execution tuple above, action_binding, and authority_ref.

No matching COMMIT means no forwarding admission.

### Handoff rule

The existing cMCP forwarding operation remains the effect transition. The integration seam is immediately before upstream invocation.

The integration MUST NOT introduce a second upstream forwarding path.

## Evidence continuity

commit_id -> execution_id -> call_id -> tool_name -> request_payload_hash -> policy/config identity -> cMCP audit entry -> TRACE claim

cMCP remains authoritative for its own audit and TRACE semantics. EABC does not claim that cMCP audit evidence proves an external physical effect.

## Failure semantics

1. no commit / not started;
2. commit refused before forwarding;
3. forwarding may have started but terminal outcome is unknown;
4. upstream response received;
5. terminal evidence durable.

An outcome-unknown state is not permission to replay the same COMMIT.

## Non-goals

- native EABC conformance by cMCP;
- hardware enforcement of EABC;
- exactly-once external execution;
- physical safety;
- proof that an external physical effect occurred;
- replacement of Cedar, TEE attestation, or TRACE.

## Decisive integration test

The first real implementation experiment should answer one question:

> Does every production-reachable path capable of causing the declared MCP-forwarding consequence pass through the same EABC admission boundary?

A private direct call to the internal forwarding method is not sufficient evidence of a production bypass. Conversely, a production-reachable forwarding path that can cause the same consequence without a valid EABC COMMIT would be material evidence that the declared consequence is not exclusively mediated by the proposed boundary.