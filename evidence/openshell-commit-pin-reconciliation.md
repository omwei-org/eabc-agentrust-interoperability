# OpenShell commit pin reconciliation

## Status

**Source-level regression evidence:** PASS at `b58e24c9dabd6d4bcf2b7186592d3ad50646541b` (Run #12).  
**Runtime-validation baseline requested by issue #6:** `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`.  
**Baseline-vs-target equivalence:** NOT ESTABLISHED.  
**Runtime result:** NOT TESTED.

## Why there are two SHAs

Issue #6 asks that runtime validation use OpenShell commit `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317`, or explicitly record a reviewed newer commit.

The existing targeted-regression workflow pins `b58e24c9dabd6d4bcf2b7186592d3ad50646541b`. Run #12 successfully checked out that exact commit and passed its three named source-level regression tests. The target commit's message is `fix(supervisor): report plaintext scheme to middleware (#4397)`; it is not, by its commit message alone, evidence that it is the right runtime baseline for every test family.

The two commits are different. A successful run at `b58e24c` must not be represented as a runtime run at `a4c848a`, and results from one target must not silently be attributed to the other.

## Required reconciliation before runtime results are recorded

1. Keep Run #12 as source-level regression evidence for the exact SHA it tested.
2. Use `a4c848adbddd0b4732fd70ddcf8a563a5b1e9317` as the initial runtime-validation baseline unless a test-specific reason to use another commit is recorded.
3. For each source-level test reused in runtime validation, verify that the test exists and has the intended semantics at the chosen SHA; record its exact test name and source path.
4. If a newer SHA is selected for a test family, record the reason, relevant changed files, and the exact claims that the newer source supports.
5. Keep test results separated by SHA. Do not combine them into one aggregate PASS.
6. Runtime validation still requires an isolated lab, synthetic credentials, a harmless canary effect, and independent effect-side observation. Unit-test success is not a substitute.

## Current decision

No baseline-versus-target runtime comparison has been executed in this record. The broader EABC/SLC assessment remains **INCONCLUSIVE**. GEN/REV/CTL, network alternate-path, filesystem-share, Sentry, and integrated rows remain **NOT TESTED** unless supported by their own pinned execution evidence.
