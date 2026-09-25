from pathlib import Path
UPSTREAM=Path("upstream/cmcp/src/cmcp_runtime/mcp/proxy.py")
IMPORT="from cmcp_runtime.audit.chain import AuditChain\n"
ANCHOR="        # Step 5b: forward to the attested upstream MCP server.\n"
NATIVE='''        finalization.execution_id = execution_id
        return self._refuse_execution(
            finalization, entry, call_id, tool_name, request_payload_hash,
            sensitivity_before, workflow_id, t0, called_at,
            rule="execution:unavailable",
            deny_reason="execution_correlation_unavailable",
        )'''
HOOK="""        # T35 EXPERIMENTAL: external authority-state validation.
        provider = getattr(self, "_t35_authority_provider", None)
        t35_commit = getattr(self, "_t35_commit", None)
        if t35_commit is not None and provider is not None:
            current_epoch = provider.current_epoch()
            self._t35_adapter.validate(
                t35_commit,
                agent_identity=self._session.session_id,
                execution_id=execution_id,
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                policy_id=getattr(self, "_t35_policy_id", "t35-policy"),
                current_authority_epoch=current_epoch,
            )

"""
def main():
    text=UPSTREAM.read_text()
    if "T35 EXPERIMENTAL: external authority-state validation" in text: return
    if IMPORT not in text or ANCHOR not in text or NATIVE not in text:
        raise SystemExit("T35 patch anchor missing")
    text=text.replace(IMPORT,IMPORT+"from eabc_profile import EABCMCPAdapter\n",1)
    text=text.replace(NATIVE,"        finalization.execution_id = execution_id\n        return None",1)
    text=text.replace(ANCHOR,HOOK+ANCHOR,1)
    UPSTREAM.write_text(text)
if __name__=="__main__": main()
