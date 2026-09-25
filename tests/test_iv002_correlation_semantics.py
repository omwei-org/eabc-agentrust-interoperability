"""IV-002 — controlled cross-domain evidence correlation semantics.

This test encodes the IV-002 decision matrix. It does not claim native
TRACE × EABC production interoperability. The bridge is explicit test
instrumentation and remains separate from native source semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Correlation(str, Enum):
    CORRELATED = "CORRELATED"
    NOT_CORRELATED = "NOT_CORRELATED"
    UNRESOLVED = "UNRESOLVED"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"


@dataclass(frozen=True)
class Evidence:
    execution_identity: str
    action_identity: str
    timestamp: int
    execution_context: str
    integrity: bool = True
    contradiction: bool = False
    rejected: bool = False
    execution_divergence: bool = False


def correlate(left: Evidence, right: Evidence) -> tuple[Correlation, str | None]:
    if not left.integrity or not right.integrity:
        return Correlation.INTEGRITY_FAILURE, "UNDETERMINED"

    if left.contradiction or right.contradiction:
        return Correlation.NOT_CORRELATED, None

    if left.execution_identity != right.execution_identity:
        return Correlation.UNRESOLVED, None

    if left.execution_context != right.execution_context:
        return Correlation.UNRESOLVED, None

    if left.action_identity != right.action_identity:
        return Correlation.UNRESOLVED, None

    if left.timestamp != right.timestamp:
        return Correlation.UNRESOLVED, None

    secondary = None
    if left.execution_divergence or right.execution_divergence:
        secondary = "EXECUTION_DIVERGENCE"
    elif left.rejected or right.rejected:
        secondary = "REJECTED"

    return Correlation.CORRELATED, secondary


def base_pair() -> tuple[Evidence, Evidence]:
    return (
        Evidence("exec-001", "action-001", 100, "ctx-A"),
        Evidence("exec-001", "action-001", 100, "ctx-A"),
    )


def test_iv002_e1_nominal_correlates_without_shared_identifier():
    left, right = base_pair()
    result = correlate(left, right)
    assert result == (Correlation.CORRELATED, None)


def test_iv002_e2_correlation_is_distinct_from_execution_consistency():
    left, right = base_pair()
    right = Evidence(
        right.execution_identity,
        "applied-action-different",
        right.timestamp,
        right.execution_context,
        execution_divergence=True,
    )

    # The test bridge supplies the execution-trajectory binding separately;
    # action divergence is therefore represented as a secondary state.
    left = Evidence(
        left.execution_identity,
        left.action_identity,
        left.timestamp,
        left.execution_context,
        execution_divergence=True,
    )
    result = correlate(left, right)
    assert result == (Correlation.CORRELATED, "EXECUTION_DIVERGENCE")


def test_iv002_e3_missing_binding_remains_unresolved():
    left, right = base_pair()
    right = Evidence(
        "exec-unknown",
        right.action_identity,
        right.timestamp,
        right.execution_context,
    )
    assert correlate(left, right) == (Correlation.UNRESOLVED, None)


def test_iv002_e4_positive_contradiction_blocks_correlation():
    left, right = base_pair()
    right = Evidence(
        right.execution_identity,
        right.action_identity,
        right.timestamp,
        right.execution_context,
        contradiction=True,
    )
    assert correlate(left, right) == (Correlation.NOT_CORRELATED, None)


def test_iv002_e5_rejection_does_not_erase_correlation():
    left, right = base_pair()
    right = Evidence(
        right.execution_identity,
        right.action_identity,
        right.timestamp,
        right.execution_context,
        rejected=True,
    )
    assert correlate(left, right) == (Correlation.CORRELATED, "REJECTED")


def test_iv002_e6_integrity_failure_is_not_non_correlation():
    left, right = base_pair()
    right = Evidence(
        right.execution_identity,
        right.action_identity,
        right.timestamp,
        right.execution_context,
        integrity=False,
    )
    assert correlate(left, right) == (
        Correlation.INTEGRITY_FAILURE,
        "UNDETERMINED",
    )
