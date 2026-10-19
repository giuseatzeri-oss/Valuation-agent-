import pytest

from vt_valuation_agent.valuation.wacc import cost_of_equity_capm, relever_beta, unlever_beta, wacc


def test_capm_with_premia():
    assert cost_of_equity_capm(0.04, 1.2, 0.05, size_premium=0.01) == pytest.approx(0.04 + 0.06 + 0.01)


def test_wacc_from_weights():
    r = wacc(cost_of_equity=0.10, pre_tax_cost_of_debt=0.05, tax_rate=0.25, debt_weight=0.40)
    assert r.after_tax_cost_of_debt == pytest.approx(0.0375)
    assert r.wacc == pytest.approx(0.6 * 0.10 + 0.4 * 0.0375)


def test_wacc_from_market_values_matches_weights():
    a = wacc(0.10, 0.05, 0.25, equity_value=600, debt_value=400)
    b = wacc(0.10, 0.05, 0.25, debt_weight=0.40)
    assert a.wacc == pytest.approx(b.wacc)


def test_wacc_requires_structure():
    with pytest.raises(ValueError):
        wacc(0.10, 0.05, 0.25)


def test_beta_round_trip():
    bu = unlever_beta(1.3, debt_to_equity=0.5, tax_rate=0.25)
    assert bu == pytest.approx(1.3 / 1.375)
    assert relever_beta(bu, 0.5, 0.25) == pytest.approx(1.3)
