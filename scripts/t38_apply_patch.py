from pathlib import Path
UPSTREAM=Path("upstream/cmcp/src/cmcp_runtime/mcp/proxy.py")
IMPORT="from cmcp_runtime.audit.chain import AuditChain\n";ANCHOR="        # Step 5b: forward to the attested upstream MCP server.\n"
NATIVE='''        finalization.execution_id = execution_id
        return self._refuse_execution(
            finalization, entry, call_id, tool_name, request_payload_hash,
            sensitivity_before, workflow_id, t0, called_at,
            rule="execution:unavailable",
            deny_reason="execution_correlation_unavailable",
        )'''
HOOK="""        # T38 EXPERIMENTAL: atomic authority snapshot / commit linearization.
        authority = getattr(self, "_t38_authority", None)
        snap = getattr(self, "_t38_snapshot", None)
        commit = getattr(self, "_t38_commit", None)
        if authority is not None and snap is not None and commit is not None:
            authority.consume(snap)
            self._t38_adapter.validate(
                commit, agent_identity=self._session.session_id,
                execution_id=execution_id, call_id=call_id,
                tool_name=tool_name, arguments=arguments,
                policy_id=getattr(self, "_t38_policy_id", "t38-policy"),
                current_authority_epoch=snap.epoch,
            )

"""
def main():
    text=UPSTREAM.read_text()
    if "T38 EXPERIMENTAL: atomic authority snapshot / commit linearization" in text:return
    if IMPORT not in text or ANCHOR not in text or NATIVE not in text:raise SystemExit("T38 patch anchor missing")
    text=text.replace(IMPORT,IMPORT+"from eabc_profile import EABCMCPAdapter\n",1).replace(NATIVE,"        finalization.execution_id = execution_id\n        return None",1).replace(ANCHOR,HOOK+ANCHOR,1)
    UPSTREAM.write_text(text)
if __name__=="__main__":main()
