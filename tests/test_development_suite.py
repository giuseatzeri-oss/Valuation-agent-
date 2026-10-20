"""Residential absorption, development cash flow, equity waterfall, and the
worked examples printed in VT Capital's Institutional SOP v2.0."""

import pytest

from vt_valuation_agent.valuation.development import CostItem, development_cash_flow
from vt_valuation_agent.valuation.finance_math import irr
from vt_valuation_agent.valuation.hotel_fixvar import ExpenseLine, fixvar_proforma
from vt_valuation_agent.valuation.hotel_market import Competitor, SubjectHotel, market_study
from vt_valuation_agent.valuation.residential import PaymentSchedule, UnitType, residential_absorption
from vt_valuation_agent.valuation.waterfall import WaterfallTier, equity_waterfall


# --- SOP v2 worked examples -------------------------------------------------

def test_sop_v2_rnaadr_illustration():
    """120 rooms open 300 days at 65% give 23,400 accommodated room nights; 60% leisure gives 14,040."""
    comp = Competitor(name="X", rooms=120, occupancy=0.65, fraction_open=300 / 365, segmentation={"leisure": 0.6, "commercial": 0.4})
    subject = SubjectHotel(rooms=10, opening_fraction=[1.0], penetration={"leisure": [1.0], "commercial": [1.0]})
    r = market_study([comp], subject, {"leisure": 0, "commercial": 0}, {"leisure": 100, "commercial": 100}, years=1)
    assert r.base_year[0].room_nights == pytest.approx(23_400)
    assert r.base_year_demand_by_segment["leisure"] == pytest.approx(14_040)


def test_sop_v2_fixvar_worked_example():
    """EUR 1.0m base rooms expense, 60% fixed, occupancy 70% to 80%: 600,000 + 457,143 = 1,057,143 before inflation."""
    r = fixvar_proforma(
        rooms=100, occupancy=[0.80], adr=[100.0], base_occupancy=0.70, base_adr=100.0, other_revenues=[],
        departmental_expenses=[ExpenseLine(name="rooms_expense", base_amount=1_000_000, fixed_pct=0.6, index="occupancy", department="rooms")],
        undistributed_expenses=[], fixed_charges=[], inflation=0.0,
    )
    assert r.years[0].departmental_expenses["rooms_expense"] == pytest.approx(1_057_142.86, abs=1)


# --- residential ------------------------------------------------------------

def test_residential_receipt_timing():
    ut = UnitType(name="villa", units=10, net_saleable_sqm=100, price_per_sqm=5_000, launch_year=1, absorption_per_year=5)
    r = residential_absorption([ut], PaymentSchedule(completion_year=3, at_reservation=0.1, during_construction=0.3, at_completion=0.6),
                               years=4, selling_costs_pct=0.0)
    gross = [y.gross_receipts for y in r.years]
    assert gross[0] == pytest.approx(250_000)        # 5 reservations
    assert gross[1] == pytest.approx(250_000 + 750_000)  # year-2 reservations + year-1 construction share
    assert gross[2] == pytest.approx(1_500_000 + 2_250_000)  # completions: 60% of year-1 sales, 90% of year-2 sales
    assert gross[3] == 0
    assert sum(gross) == pytest.approx(5_000_000)
    assert r.sell_out_year_by_type["villa"] == 2
    assert r.average_price_per_sqm == pytest.approx(5_000)


def test_residential_costs_and_growth():
    ut = UnitType(name="branded", units=2, net_saleable_sqm=100, price_per_sqm=7_400, absorption_per_year=1, branded=True)
    r = residential_absorption([ut], PaymentSchedule(completion_year=1), years=3, price_growth=0.05, selling_costs_pct=0.03, brand_fee_pct=0.04)
    assert r.years[0].gross_receipts == pytest.approx(740_000)
    assert r.years[1].gross_receipts == pytest.approx(740_000 * 1.05)
    assert r.years[0].net_receipts == pytest.approx(740_000 * (1 - 0.03 - 0.04))
    with pytest.raises(ValueError):
        residential_absorption([ut], PaymentSchedule(completion_year=1, at_reservation=0.5), years=2)


# --- development ------------------------------------------------------------

def test_development_cash_flow_unlevered_and_residual():
    noi = [0.0, 0.0, 30.0, 32.0, 34.0]
    r = development_cash_flow(
        land_cost=100.0, cost_items=[CostItem(name="build", amount=200.0, start_year=1, duration_years=1, profile="straight")],
        operating_noi=noi, exit_year=5, terminal_cap_rate=0.08, exit_noi=35.0, project_hurdle_rate=0.10, selling_costs_pct=0.0,
        solve_residual_land_value=True,
    )
    expected = [-100.0, -200.0, 0.0, 30.0, 32.0, 34.0 + 35.0 / 0.08]
    assert r.unlevered_cash_flows == pytest.approx(expected)
    assert r.unlevered_irr == pytest.approx(irr(expected))
    # the discounted residual sets NPV at the hurdle to zero
    npv0 = sum(cf / 1.1**t for t, cf in enumerate([0.0] + expected[1:]))
    assert r.discounted_residual_land_value == pytest.approx(npv0)
    again = development_cash_flow(
        land_cost=r.discounted_residual_land_value, cost_items=[CostItem(name="build", amount=200.0, start_year=1, profile="straight")],
        operating_noi=noi, exit_year=5, terminal_cap_rate=0.08, exit_noi=35.0, project_hurdle_rate=0.10, selling_costs_pct=0.0,
    )
    assert again.unlevered_irr == pytest.approx(0.10, abs=1e-6)
    assert r.equity_cash_flows == pytest.approx(expected)  # no debt


def test_development_with_construction_loan():
    r = development_cash_flow(
        land_cost=50.0, cost_items=[CostItem(name="build", amount=100.0, start_year=1, duration_years=2, profile="straight")],
        operating_noi=[0.0, 0.0, 12.0, 12.0], exit_year=4, terminal_cap_rate=0.08, exit_noi=12.5, project_hurdle_rate=0.09,
        construction_ltc=0.5, interest_rate=0.06, loan_fees_pct=0.0, selling_costs_pct=0.0,
    )
    y = {row.year: row for row in r.years}
    assert y[1].loan_draw == pytest.approx(25.0) and y[2].loan_draw == pytest.approx(25.0)
    assert y[2].interest_capitalised == pytest.approx(25.0 * 0.06)       # pre-opening interest rolls up
    assert y[3].interest_paid == pytest.approx(y[2].loan_balance_end * 0.06)  # paid once open
    assert y[4].principal_repaid == pytest.approx(y[3].loan_balance_end)
    assert y[4].loan_balance_end == pytest.approx(0.0)
    assert r.peak_debt > 50
    assert r.equity_irr is not None and r.equity_multiple is not None
    assert r.peak_equity == pytest.approx(-min(row.cumulative_equity for row in r.years))


def test_s_curve_weights_sum_to_amount():
    r = development_cash_flow(
        land_cost=0.0, cost_items=[CostItem(name="c", amount=90.0, start_year=0, duration_years=3)],
        operating_noi=[0, 0, 0, 10, 10], exit_year=5, terminal_cap_rate=0.1, exit_noi=10, project_hurdle_rate=0.08,
        solve_residual_land_value=False,
    )
    spend = [row.development_costs for row in r.years]
    assert sum(spend) == pytest.approx(90.0)
    assert spend[1] > spend[0] and spend[1] > spend[2]  # peak in the middle


# --- waterfall --------------------------------------------------------------

def test_waterfall_pref_and_promote_hand_calculation():
    tiers = [WaterfallTier(hurdle_irr=0.08, capital_share=1.0), WaterfallTier(hurdle_irr=None, capital_share=0.8)]
    r = equity_waterfall([-100.0, 0.0, 0.0, 150.0], tiers)
    pref = 100 * 1.08**3
    last = r.periods[-1]
    assert last.by_tier["tier_1"] == pytest.approx(pref)
    assert last.promote == pytest.approx((150 - pref) * 0.2)
    assert last.to_capital == pytest.approx(pref + (150 - pref) * 0.8)
    assert r.lp_irr > 0.08
    assert r.capital_irr_before_promote == pytest.approx(irr([-100, 0, 0, 150]))


def test_waterfall_full_catch_up_delivers_target_promote():
    tiers = [WaterfallTier(hurdle_irr=0.08, capital_share=1.0), WaterfallTier(hurdle_irr=None, capital_share=0.8)]
    r = equity_waterfall([-100.0, 0.0, 0.0, 150.0], tiers, catch_up_pct=1.0, catch_up_to_promote=0.2)
    assert r.total_promote == pytest.approx(0.2 * 50.0)
    assert r.promote_share_of_profit == pytest.approx(0.2)
    assert r.total_to_capital == pytest.approx(140.0)


def test_waterfall_multi_hurdle_and_coinvest():
    tiers = [WaterfallTier(hurdle_irr=0.08, capital_share=1.0), WaterfallTier(hurdle_irr=0.15, capital_share=0.8),
             WaterfallTier(hurdle_irr=None, capital_share=0.6)]
    flows = [-100.0, 10.0, 10.0, 10.0, 160.0]
    r = equity_waterfall(flows, tiers, lp_capital_share=0.9)
    assert sum(p.distribution for p in r.periods) == pytest.approx(sum(p.to_capital + p.promote for p in r.periods))
    assert sum(p.lp_contribution for p in r.periods) == pytest.approx(90.0)
    # LP never beats the deal IRR once promote is paid; GP (co-invest + promote) beats it
    assert r.lp_irr < r.capital_irr_before_promote < r.gp_irr
    with pytest.raises(ValueError):
        equity_waterfall(flows, [WaterfallTier(hurdle_irr=0.08, capital_share=1.0)])
