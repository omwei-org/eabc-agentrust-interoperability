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
HOOK="""        # T36 EXPERIMENTAL: authority-state provenance validation.
        state = getattr(self, "_t36_state", None)
        verifier = getattr(self, "_t36_verifier", None)
        t36_commit = getattr(self, "_t36_commit", None)
        if state is not None and verifier is not None and t36_commit is not None:
            current_epoch = getattr(self, "_t36_current_epoch", state.authority_epoch)
            verifier.verify(state, int(__import__("time").time()), current_epoch)
            self._t36_adapter.validate(
                t36_commit,
                agent_identity=self._session.session_id,
                execution_id=execution_id,
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                policy_id=getattr(self, "_t36_policy_id", "t36-policy"),
                current_authority_epoch=current_epoch,
            )

"""
def main():
    text=UPSTREAM.read_text()
    if "T36 EXPERIMENTAL: authority-state provenance validation" in text: return
    if IMPORT not in text or ANCHOR not in text or NATIVE not in text: raise SystemExit("T36 patch anchor missing")
    text=text.replace(IMPORT,IMPORT+"from eabc_profile import EABCMCPAdapter\n",1)
    text=text.replace(NATIVE,"        finalization.execution_id = execution_id\n        return None",1)
    text=text.replace(ANCHOR,HOOK+ANCHOR,1)
    UPSTREAM.write_text(text)
if __name__=="__main__": main()
