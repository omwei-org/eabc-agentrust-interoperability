# T26.7 — Evidence Manifest Finalization

The repository now contains a CI workflow that builds the content-addressed evidence manifest from the exact checked-out repository bytes.

## Procedure

1. Checkout the repository revision.
2. Execute `tools/build_t26_7_manifest.py`.
3. Compute SHA-256 for every declared artifact.
4. Run the manifest verifier.
5. Emit the generated manifest as the frozen candidate.

The workflow does not claim a frozen release merely because the manifest file exists. The final status becomes frozen only after a successful CI run at the intended release revision.

## Integrity rule

No manually supplied SHA-256 values are accepted.

The hash is calculated from the bytes present in the CI checkout.

## Status

**FINALIZATION WORKFLOW READY**

**FROZEN: NOT YET CLAIMED**
