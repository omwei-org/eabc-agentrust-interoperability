from pathlib import Path

UPSTREAM = Path("upstream/cmcp/src/cmcp_runtime/mcp/proxy.py")
IMPORT = "from cmcp_runtime.audit.chain import AuditChain\n"
ANCHOR = "        # Step 5b: forward to the attested upstream MCP server.\n"

HOOK = """        # T32 EXPERIMENTAL: execution-boundary exclusivity hook.
        t32_mode = getattr(self, "_t32_mode", "OPTIONAL")
        t32_adapter = getattr(self, "_t30_3_adapter", None)
        t32_commit = getattr(self, "_t30_3_commit", None)
        if t32_mode == "MANDATORY" and execution_id is None:
            raise PermissionError("EABC_EXECUTION_ADMISSION_REQUIRED")
        if execution_id is not None and t32_adapter is not None:
            if t32_commit is None:
                raise PermissionError("EABC_NO_COMMIT")
            t32_adapter.validate(
                t32_commit,
                agent_identity=self._session.session_id,
                execution_id=execution_id,
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                policy_id=getattr(self, "_t30_3_policy_id", "t32-policy"),
                agent_identity=self._session.session_id,
                execution_id=execution_id,
            )

"""
NATIVE = '''        finalization.execution_id = execution_id
        return self._refuse_execution(
            finalization, entry, call_id, tool_name, request_payload_hash,
            sensitivity_before, workflow_id, t0, called_at,
            rule="execution:unavailable",
            deny_reason="execution_correlation_unavailable",
        )'''

def main():
    text = UPSTREAM.read_text()
    if "T32 EXPERIMENTAL: execution-boundary exclusivity hook." in text:
        return
    if IMPORT not in text or ANCHOR not in text or NATIVE not in text:
        raise SystemExit("T32 patch anchor missing")
    text = text.replace(IMPORT, IMPORT + "from eabc_profile import EABCMCPAdapter\n", 1)
    text = text.replace(NATIVE, "        finalization.execution_id = execution_id\n        return None", 1)
    text = text.replace(ANCHOR, HOOK + ANCHOR, 1)
    UPSTREAM.write_text(text)

if __name__ == "__main__":
    main()
