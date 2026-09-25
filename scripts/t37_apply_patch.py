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
HOOK="""        # T37 EXPERIMENTAL: authority-key lifecycle validation.
        authority = getattr(self, "_t37_authority", None)
        state = getattr(self, "_t37_state", None)
        commit = getattr(self, "_t37_commit", None)
        if authority is not None and state is not None and commit is not None:
            authority.verify(state, int(__import__("time").time()),
                             getattr(self, "_t37_current_epoch", state.authority_epoch))
            self._t37_adapter.validate(
                commit,
                agent_identity=self._session.session_id,
                execution_id=execution_id,
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                policy_id=getattr(self, "_t37_policy_id", "t37-policy"),
                current_authority_epoch=getattr(self, "_t37_current_epoch", state.authority_epoch),
            )

"""
def main():
    text=UPSTREAM.read_text()
    if "T37 EXPERIMENTAL: authority-key lifecycle validation" in text:return
    if IMPORT not in text or ANCHOR not in text or NATIVE not in text:raise SystemExit("T37 patch anchor missing")
    text=text.replace(IMPORT,IMPORT+"from eabc_profile import EABCMCPAdapter\n",1)
    text=text.replace(NATIVE,"        finalization.execution_id = execution_id\n        return None",1)
    text=text.replace(ANCHOR,HOOK+ANCHOR,1); UPSTREAM.write_text(text)
if __name__=="__main__":main()
