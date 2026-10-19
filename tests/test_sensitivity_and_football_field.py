import pytest

from vt_valuation_agent.valuation.football_field import ValuationRange, football_field
from vt_valuation_agent.valuation.sensitivity import dcf_sensitivity


def test_sensitivity_grid_shape_and_monotonicity():
    t = dcf_sensitivity([100, 110, 120], [0.08, 0.10, 0.12], terminal_growth_rates=[0.01, 0.02, 0.03])
    assert len(t.values) == 3 and all(len(r) == 3 for r in t.values)
    # value falls with the discount rate and rises with growth
    assert t.values[0][1] > t.values[1][1] > t.values[2][1]
    assert t.values[1][0] < t.values[1][1] < t.values[1][2]
    assert "discount rate" in t.to_markdown()


def test_sensitivity_marks_undefined_cells():
    t = dcf_sensitivity([100], [0.05], terminal_growth_rates=[0.04, 0.06])
    assert t.values[0][0] is not None and t.values[0][1] is None


def test_football_field_normalises_bases():
    ranges = [
        ValuationRange(method="DCF", low=900, high=1100, basis="enterprise", weight=2),
        ValuationRange(method="Comps", low=700, high=900, basis="equity"),
        ValuationRange(method="52w", low=70, high=90, basis="per_share"),
    ]
    ff = football_field(ranges, net_debt=100, shares_outstanding=10)
    by = {b.method: b for b in ff.bars}
    assert by["Comps"].enterprise_mid == pytest.approx(900)
    assert by["52w"].equity_mid == pytest.approx(800)
    assert by["52w"].enterprise_low == pytest.approx(800)
    # weighted mid: (1000*2 + 900*1 + 900*1) / 4 = 950
    assert ff.weighted_mid["enterprise"] == pytest.approx(950)
    assert ff.overall_low["enterprise"] == pytest.approx(800)
    assert ff.overall_high["enterprise"] == pytest.approx(1100)
    assert ff.weighted_mid["per_share"] == pytest.approx(85)


def test_football_field_per_share_requires_shares():
    with pytest.raises(ValueError):
        football_field([ValuationRange(method="x", low=1, high=2, basis="per_share")])
