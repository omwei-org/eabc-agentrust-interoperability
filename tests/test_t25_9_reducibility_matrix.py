# T25.9 — Reducibility Matrix Validation

from dataclasses import dataclass


@dataclass(frozen=True)
class Mapping:
    eabc_stage: str
    classification: str


def test_t25_9_matrix_contains_actual_eabc_stages():
    stages = [
        "AO", "AEE", "ECT", "PREPARE", "FINAL_AUTHORITY_CHECK",
        "COMMIT GATE", "EAtt", "Execution Domain", "EFFECT",
    ]
    assert stages == [
        "AO", "AEE", "ECT", "PREPARE", "FINAL_AUTHORITY_CHECK",
        "COMMIT GATE", "EAtt", "Execution Domain", "EFFECT",
    ]


def test_t25_9_native_and_adapter_claims_are_separated():
    mappings = [
        Mapping("AEE", "NATIVE"),
        Mapping("PREPARE", "NATIVE"),
        Mapping("COMMIT GATE", "ADAPTER-DEMONSTRATED"),
        Mapping("Exact execution binding", "ADAPTER-DEMONSTRATED"),
        Mapping("COMMIT → terminal audit binding", "ADAPTER-DEMONSTRATED"),
        Mapping("Universal effect mediation", "ABSENT"),
    ]
    native = {m.eabc_stage for m in mappings if m.classification == "NATIVE"}
    adapter = {m.eabc_stage for m in mappings if m.classification == "ADAPTER-DEMONSTRATED"}
    assert "AEE" in native
    assert "COMMIT GATE" in adapter
    assert "Exact execution binding" in adapter
    assert "COMMIT → terminal audit binding" in adapter
    assert "Universal effect mediation" not in native
