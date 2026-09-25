from pathlib import Path

UPSTREAM = Path("upstream/cmcp/src/cmcp_runtime/mcp/proxy.py")
IMPORT = "from cmcp_runtime.audit.chain import AuditChain\n"
ANCHOR = "        # Step 5b: forward to the attested upstream MCP server.\n"
NATIVE = '''        finalization.execution_id = execution_id
        return self._refuse_execution(
            finalization, entry, call_id, tool_name, request_payload_hash,
            sensitivity_before, workflow_id, t0, called_at,
            rule="execution:unavailable",
            deny_reason="execution_correlation_unavailable",
        )'''

HOOK = """        # T34 EXPERIMENTAL: strict authority-state validation at forwarding boundary.
        t34_adapter = getattr(self, "_t34_adapter", None)
        t34_commit = getattr(self, "_t34_commit", None)
        if t34_commit is not None:
            before_consume = getattr(self, "_t34_before_consume", None)
            if before_consume is not None:
                before_consume()
            current_epoch = getattr(self, "_t34_authority_epoch", None)
            t34_adapter.validate(
                t34_commit,
                agent_identity=self._session.session_id,
                execution_id=execution_id,
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                policy_id=getattr(self, "_t34_policy_id", "t34-policy"),
                current_authority_epoch=current_epoch,
            )

"""
def main():
    text = UPSTREAM.read_text()
    if "T34 EXPERIMENTAL: strict authority-state validation" in text:
        return
    if IMPORT not in text or ANCHOR not in text or NATIVE not in text:
        raise SystemExit("T34 patch anchor missing")
    text = text.replace(IMPORT, IMPORT + "from eabc_profile import EABCMCPAdapter\n", 1)
    text = text.replace(NATIVE, "        finalization.execution_id = execution_id\n        return None", 1)
    text = text.replace(ANCHOR, HOOK + ANCHOR, 1)
    UPSTREAM.write_text(text)
if __name__ == "__main__":
    main()
