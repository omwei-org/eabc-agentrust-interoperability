# T30.3 runtime patch artifact

The runtime experiment patches only the pinned cMCP execution-correlation
revision:

`f8743e013786b094caaa70c336519834e73c74d5`

The patch is applied in CI to a disposable upstream checkout. The upstream
repository is not modified by this experiment.

## Native versus experimental

Native cMCP remains responsible for request handling, execution-correlation
parsing, Cedar authorization, catalog/upstream resolution, existing forwarding,
and audit/TRACE.

The experiment adds only EABC COMMIT validation, execution/action binding
validation, and the handoff check immediately before forwarding.

A successful run therefore demonstrates:

**pinned cMCP runtime + repository-added EABC hook**

It does not demonstrate native EABC support in cMCP.

## Race seam

The patch exposes an experiment-only callback immediately after EABC validation
and immediately before forwarding. This is a measurement seam for the TOCTOU
experiment.

If authority is invalidated at this point and forwarding still proceeds, the
experiment has observed a validation-to-forward interval. Whether that interval
is a security defect depends on the authority model and production integration;
the result is not automatically attributed to cMCP.
