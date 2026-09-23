# T27 — Evidence and Provenance

T27 uses checked-in test vectors and provenance. The final reproduction manifest is generated in CI and is not checked in because its `git_commit` field would make a checked-in manifest self-referential. The generated manifest content-addresses the T27 documentation and evidence inputs and binds them to the CI checkout revision.