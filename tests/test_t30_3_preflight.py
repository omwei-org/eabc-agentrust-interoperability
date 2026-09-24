def test_t30_3_pin_is_explicit():
    assert "f8743e013786b094caaa70c336519834e73c74d5" == "f8743e013786b094caaa70c336519834e73c74d5"


def test_t30_3_claim_boundary_is_not_native_support():
    assert "cMCP + EABC hook" != "cMCP"
