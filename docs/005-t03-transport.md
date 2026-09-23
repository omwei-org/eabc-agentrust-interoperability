# 005 — T03 Transport-Level Observation

The capture server is an execution-domain observation point. It records the exact HTTP request body received and computes SHA-256 over that body.

This first transport test validates the capture mechanism and canonical request comparison. It does not yet drive a real cMCP instance against the capture server.

Current classification:
- capture server: DEMONSTRATED
- exact request digesting: DEMONSTRATED
- real cMCP → capture server binding: NOT DEMONSTRATED
- prevention of adversarial substitution: NOT DEMONSTRATED

The next step is to configure a real cMCP proxy instance to forward to this local endpoint and compare the authorized request digest with the received upstream request digest.
