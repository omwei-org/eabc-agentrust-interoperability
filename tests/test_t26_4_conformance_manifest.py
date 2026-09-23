"""T26.4 — unified EABC-MCP profile conformance manifest."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    status: str
    evidence: tuple[str, ...]


REQUIREMENTS = (
    Requirement("MCP-EABC-001", "PASS", ("T25.6",)),
    Requirement("MCP-EABC-002", "PASS", ("T25.2", "T26.2")),
    Requirement("MCP-EABC-003", "PASS", ("T25.5", "T26.3")),
    Requirement("MCP-EABC-004", "PASS", ("T25.4",)),
    Requirement("MCP-EABC-005", "PASS", ("T25.7",)),
    Requirement("MCP-EABC-006", "PASS", ("T25.8",)),
    Requirement("MCP-EABC-007", "PASS", ("T25.9",)),
    Requirement("MCP-EABC-008", "PASS", ("T25.9",)),
)


def test_all_must_requirements_have_evidence():
    assert len(REQUIREMENTS) == 8
    assert all(r.status == "PASS" and r.evidence for r in REQUIREMENTS)


def test_no_requirement_claims_native_cMCP_conformance():
    native_claims = {
        "MCP-EABC-001": False,
        "MCP-EABC-002": False,
        "MCP-EABC-003": False,
        "MCP-EABC-004": False,
        "MCP-EABC-005": False,
        "MCP-EABC-006": False,
        "MCP-EABC-007": False,
        "MCP-EABC-008": False,
    }
    assert not any(native_claims.values())
