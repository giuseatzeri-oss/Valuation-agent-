import pytest

from vt_valuation_agent.valuation.dcf import dcf_valuation, project_free_cash_flows


def test_perpetuity_dcf_hand_calculation():
    # PV of 100, 110, 121 at 10% is 272.73; TV = 121*1.02/0.08 = 1542.75, PV = 1159.09
    r = dcf_valuation([100, 110, 121], 0.10, terminal_growth=0.02, net_debt=100, shares_outstanding=10)
    assert r.sum_pv_cash_flows == pytest.approx(272.727, rel=1e-4)
    assert r.terminal_value == pytest.approx(1542.75)
    assert r.pv_terminal_value == pytest.approx(1542.75 / 1.331, rel=1e-6)
    assert r.enterprise_value == pytest.approx(272.727 + 1542.75 / 1.331, rel=1e-4)
    assert r.equity_value == pytest.approx(r.enterprise_value - 100)
    assert r.value_per_share == pytest.approx(r.equity_value / 10)
    assert r.terminal_method == "perpetuity_growth"


def test_mid_year_raises_value_and_discounts_tv_at_n_minus_half():
    end = dcf_valuation([100, 100, 100], 0.10, terminal_growth=0.02)
    mid = dcf_valuation([100, 100, 100], 0.10, terminal_growth=0.02, mid_year=True)
    assert mid.enterprise_value > end.enterprise_value
    assert mid.pv_terminal_value == pytest.approx(end.pv_terminal_value * 1.1**0.5)


def test_exit_multiple_method_and_implied_growth():
    r = dcf_valuation([50, 55, 60], 0.09, exit_multiple=8.0, terminal_metric=100.0)
    assert r.terminal_value == pytest.approx(800.0)
    assert r.pv_terminal_value == pytest.approx(800 / 1.09**3)
    # implied g solves TV = FCF*(1+g)/(r-g)
    g = r.implied_terminal_growth
    assert 60 * (1 + g) / (0.09 - g) == pytest.approx(800.0, rel=1e-6)


def test_exit_multiple_tv_not_shifted_by_mid_year():
    a = dcf_valuation([50, 55, 60], 0.09, exit_multiple=8.0, terminal_metric=100.0)
    b = dcf_valuation([50, 55, 60], 0.09, exit_multiple=8.0, terminal_metric=100.0, mid_year=True)
    assert a.pv_terminal_value == pytest.approx(b.pv_terminal_value)


def test_input_validation():
    with pytest.raises(ValueError):
        dcf_valuation([1, 2], 0.08)  # no terminal method
    with pytest.raises(ValueError):
        dcf_valuation([1, 2], 0.08, terminal_growth=0.03, exit_multiple=8, terminal_metric=1)
    with pytest.raises(ValueError):
        dcf_valuation([1, 2], 0.05, terminal_growth=0.06)
    with pytest.raises(ValueError):
        dcf_valuation([1, 2], 0.08, exit_multiple=8)  # missing metric


def test_warning_when_terminal_dominates():
    r = dcf_valuation([1, 1, 1], 0.06, terminal_growth=0.05)
    assert any("75%" in w for w in r.warnings)


def test_projection_schedule():
    sched = project_free_cash_flows(
        base_revenue=1000, revenue_growth=[0.10, 0.10], ebitda_margin=0.20,
        da_pct_revenue=0.05, capex_pct_revenue=0.06, nwc_pct_revenue=0.10, tax_rate=0.25,
    )
    y1 = sched[0]
    assert y1.revenue == pytest.approx(1100)
    assert y1.ebitda == pytest.approx(220)
    assert y1.ebit == pytest.approx(220 - 55)
    assert y1.taxes == pytest.approx(165 * 0.25)
    assert y1.change_in_nwc == pytest.approx(0.10 * 100)
    assert y1.unlevered_fcf == pytest.approx(165 * 0.75 + 55 - 66 - 10)
    assert sched[1].revenue == pytest.approx(1210)


def test_projection_margin_length_mismatch():
    with pytest.raises(ValueError):
        project_free_cash_flows(100, [0.1, 0.1], [0.2], 0.0, 0.0, 0.0, 0.2)
