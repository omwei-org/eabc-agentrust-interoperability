# T26.7 — Evidence Manifest Finalization

The repository contains a CI workflow that builds the content-addressed evidence manifest from the exact checked-out repository bytes.

## Procedure

1. Checkout the repository revision.
2. Execute `tools/build_t26_7_manifest.py`.
3. Compute SHA-256 for every declared artifact.
4. Run the manifest verifier.
5. Emit the generated manifest as the frozen candidate.
6. Upload the generated manifest as the CI artifact.

## Integrity rule

No manually supplied SHA-256 values are accepted.

The hash is calculated from the bytes present in the CI checkout.

The checked-in `evidence/t26-7-final-manifest.json` is only a provenance placeholder; it is not the authoritative frozen manifest and intentionally contains no artifact hashes.

## Final status

**FROZEN: YES**

Final CI run: `35895290058`  
Run conclusion: `success`  
Validated repository revision: `c7a53b1c148fa6080dd5c8553388bf560dbb5873`  
Generated artifact: `t26-7-evidence-manifest`  
Artifact digest: `sha256:1730368424f3f6031f58129e7eb3037032804c136218b6d6c9fa53247fb268c3`

The frozen manifest contains six content-addressed evidence artifacts and binds them to the exact CI checkout revision above.

The authoritative frozen manifest is the CI-generated artifact from run `35895290058`, not the checked-in placeholder.