from pathlib import Path

UPSTREAM = Path("upstream/cmcp/src/cmcp_runtime/mcp/proxy.py")
EXPECTED = "f8743e013786b094caaa70c336519834e73c74d5"
IMPORT_ANCHOR = "from cmcp_runtime.audit.chain import AuditChain\n"
HOOK_ANCHOR = "        # Step 5b: forward to the attested upstream MCP server.\n"
HOOK = '''        # T30.3 EXPERIMENTAL: EABC admission hook. This is repository-added
        # code and is not native cMCP enforcement.
        t30_3_adapter = getattr(self, "_t30_3_adapter", None)
        t30_3_commit = getattr(self, "_t30_3_commit", None)
        if execution_id is not None and t30_3_adapter is not None:
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

'''
def main():
    text = UPSTREAM.read_text()
    if "T30.3 EXPERIMENTAL: EABC admission hook" in text:
        return
    if IMPORT_ANCHOR not in text or HOOK_ANCHOR not in text:
        raise SystemExit("T30.3 patch anchor missing: upstream runtime changed.")
    text = text.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "from eabc_profile import EABCMCPAdapter\n", 1)
    text = text.replace(HOOK_ANCHOR, HOOK + HOOK_ANCHOR, 1)
    UPSTREAM.write_text(text)
if __name__ == "__main__":
    main()
