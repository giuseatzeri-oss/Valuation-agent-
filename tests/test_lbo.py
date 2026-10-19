import pytest

from vt_valuation_agent.valuation.lbo import lbo_returns, max_entry_multiple_for_irr


def test_lbo_schedule_and_returns_are_internally_consistent():
    r = lbo_returns(
        entry_ebitda=100, entry_multiple=10, exit_multiple=10, ebitda_growth=[0.0] * 5,
        leverage_multiple=5, interest_rate=0.08, tax_rate=0.25, fees_pct_ev=0.0,
    )
    y1 = r.schedule[0]
    assert r.entry_equity == pytest.approx(500)
    assert y1.interest == pytest.approx(40)
    assert y1.taxes == pytest.approx((100 - 40) * 0.25)
    assert y1.free_cash_flow == pytest.approx(100 - 40 - 15)
    assert y1.ending_debt == pytest.approx(500 - 45)
    assert r.moic == pytest.approx(r.exit_equity / r.entry_equity)
    assert (1 + r.irr) ** 5 == pytest.approx(r.moic, rel=1e-6)
    assert r.exit_equity > r.entry_equity  # deleveraging alone creates value


def test_more_leverage_raises_irr_when_deal_works():
    low = lbo_returns(100, 9, 9, [0.05] * 5, leverage_multiple=3, interest_rate=0.07, tax_rate=0.25)
    high = lbo_returns(100, 9, 9, [0.05] * 5, leverage_multiple=5, interest_rate=0.07, tax_rate=0.25)
    assert high.irr > low.irr


def test_multiple_expansion_warning():
    r = lbo_returns(100, 8, 10, [0.05] * 4, leverage_multiple=4, interest_rate=0.07, tax_rate=0.25)
    assert any("multiple expansion" in w for w in r.warnings)


def test_max_entry_multiple_solver_hits_target():
    kwargs = dict(entry_ebitda=100, exit_multiple=9, ebitda_growth=[0.06] * 5, leverage_multiple=4.5,
                  interest_rate=0.08, tax_rate=0.25)
    m = max_entry_multiple_for_irr(0.20, **kwargs)
    assert 1 < m < 40
    assert lbo_returns(entry_multiple=m, **kwargs).irr == pytest.approx(0.20, abs=2e-3)


def test_rejects_overlevered_structure():
    with pytest.raises(ValueError):
        lbo_returns(100, 5, 5, [0.0], leverage_multiple=6, interest_rate=0.08, tax_rate=0.25)
