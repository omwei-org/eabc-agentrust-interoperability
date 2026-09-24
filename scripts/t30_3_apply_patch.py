from pathlib import Path

UPSTREAM = Path("upstream/cmcp/src/cmcp_runtime/mcp/proxy.py")
EXPECTED = "f8743e013786b094caaa70c336519834e73c74d5"
IMPORT_ANCHOR = "from cmcp_runtime.audit.chain import AuditChain\n"
HOOK_ANCHOR = "        # Step 5b: forward to the attested upstream MCP server.\n"
HOOK = '''        # T30.3 EXPERIMENTAL: EABC admission hook. This is repository-added
        # code and is not native cMCP enforcement.
        t30_3_adapter = getattr(self, "_t30_3_adapter", None)
        t30_3_commit = getattr(self, "_t30_3_commit", None)
        t30_3_hook_enabled = not getattr(self, "_t30_3_disable_hook", False)
        if execution_id is not None and t30_3_adapter is not None and t30_3_hook_enabled:
            if t30_3_commit is None:
                return self._refuse_execution(
                    _finalization, entry, call_id, tool_name, request_payload_hash,
                    sensitivity_before, workflow_id, t0, called_at,
                    rule="eabc:commit_required",
                    deny_reason="eabc_commit_required",
                )
            t30_3_adapter.validate(
                t30_3_commit,
                agent_identity=self._session.session_id,
                execution_id=execution_id,
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                policy_id=getattr(self, "_t30_3_policy_id", "t30.3-policy"),
            )
            t30_3_before_forward = getattr(self, "_t30_3_before_forward", None)
            if t30_3_before_forward is not None:
                t30_3_before_forward()
            t30_3_final_authority_check = getattr(self, "_t30_3_final_authority_check", None)
            if t30_3_final_authority_check is not None:
                t30_3_final_authority_check()

'''
def main():
    text = UPSTREAM.read_text()
    if "T30.3 EXPERIMENTAL: EABC admission hook" in text:
        return
    if IMPORT_ANCHOR not in text or HOOK_ANCHOR not in text:
        raise SystemExit("T30.3 patch anchor missing: upstream runtime changed.")
    text = text.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "from eabc_profile import EABCMCPAdapter\n", 1)
    native_refusal = """        finalization.execution_id = execution_id
        return self._refuse_execution("""
    experiment_admission = """        # T30.3 EXPERIMENT ONLY: admit valid execution_id so the added
        # EABC hook below becomes the experiment's execution admission gate.
        # Native cMCP at this pinned revision would refuse this request here.
        finalization.execution_id = execution_id
        return None"""
    if native_refusal not in text:
        raise SystemExit("T30.3 native execution-refusal anchor missing.")
    text = text.replace(native_refusal, experiment_admission, 1)
    text = text.replace(HOOK_ANCHOR, HOOK + HOOK_ANCHOR, 1)
    UPSTREAM.write_text(text)
if __name__ == "__main__":
    main()
