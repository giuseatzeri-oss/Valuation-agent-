import math

import pytest

from vt_valuation_agent.valuation.hotel_fixvar import ExpenseLine, RevenueLine, fixvar_proforma
from vt_valuation_agent.valuation.hotel_market import Competitor, NewSupply, SubjectHotel, market_study
from vt_valuation_agent.valuation.mortgage_equity import loan_balance_fraction, mortgage_constant, mortgage_equity_valuation
from vt_valuation_agent.valuation.residual import residual_land_value


def two_comp_market(penetration=1.0, years=1, **kw):
    comps = [Competitor(name="A", rooms=100, occupancy=0.7, segmentation={"leisure": 1.0}),
             Competitor(name="B", rooms=100, occupancy=0.7, segmentation={"leisure": 1.0})]
    subject = SubjectHotel(rooms=100, opening_fraction=[1.0] * years, penetration={"leisure": [penetration] * years})
    return market_study(comps, subject, segment_growth={"leisure": 0.0}, base_segment_adr={"leisure": 200.0}, years=years, adr_inflation=0.0, **kw)


def test_market_study_base_year_and_fair_share_split():
    r = two_comp_market()
    assert r.base_year_demand_by_segment["leisure"] == pytest.approx(2 * 100 * 365 * 0.7)
    assert r.base_year_market_occupancy == pytest.approx(0.7)
    assert all(row.penetration_by_segment["leisure"] == pytest.approx(1.0) for row in r.base_year)
    y1 = r.projection[0]
    # three equal hotels with equal penetration share the demand equally
    assert y1.subject_fair_share == pytest.approx(1 / 3)
    assert y1.subject_room_nights == pytest.approx(51100 / 3)
    assert y1.subject_occupancy == pytest.approx(51100 / 3 / 36500)
    assert y1.subject_adr == pytest.approx(200.0)
    assert y1.subject_revpar == pytest.approx(200.0 * y1.subject_occupancy)


def test_penetration_index_raises_share():
    r = two_comp_market(penetration=1.2)
    y1 = r.projection[0]
    assert y1.subject_market_share == pytest.approx(120 / 320)
    assert y1.subject_overall_penetration == pytest.approx((120 / 320) / (1 / 3))
    assert y1.subject_occupancy == pytest.approx(51100 * 0.375 / 36500)


def test_latent_demand_growth_and_new_supply():
    comps = [Competitor(name="A", rooms=200, occupancy=0.75, segmentation={"leisure": 0.8, "meeting": 0.2}, adr=180)]
    subject = SubjectHotel(rooms=100, opening_fraction=[0.5, 1.0, 1.0], penetration={"leisure": [0.9, 1.1, 1.2], "meeting": [0.5, 0.8, 1.0]},
                           adr_index={"leisure": 1.3, "meeting": 1.1}, adr_ramp=[0.9, 1.0, 1.0])
    r = market_study(
        comps, subject, segment_growth={"leisure": 0.03, "meeting": [0.0, 0.02, 0.02]}, base_segment_adr={"leisure": 200.0, "meeting": 150.0},
        years=3, unaccommodated_demand={"leisure": 0.05}, induced_demand={"meeting": [0.0, 500.0, 1000.0]},
        new_supply=[NewSupply(name="N", rooms=80, open_year=3, first_year_fraction=0.5, penetration={"leisure": 1.0, "meeting": 1.0})],
        adr_inflation=0.03,
    )
    base_leisure = 200 * 365 * 0.75 * 0.8
    assert r.projection[0].market_demand_by_segment["leisure"] == pytest.approx(base_leisure * 1.05 * 1.03)
    assert r.projection[1].market_demand_by_segment["meeting"] == pytest.approx(200 * 365 * 0.75 * 0.2 * 1.02 + 500)
    assert r.projection[2].total_effective_rooms == pytest.approx(200 + 100 + 40)
    assert r.projection[0].subject_effective_rooms == 50
    # segment ADRs inflate and carry the subject index and ramp
    assert r.projection[0].segment_adr["leisure"] == pytest.approx(200 * 1.03 * 1.3 * 0.9)
    assert r.projection[2].segment_adr["meeting"] == pytest.approx(150 * 1.03**3 * 1.1)
    assert 0 < r.projection[2].subject_occupancy < 1


def test_market_study_validation():
    assert len(two_comp_market(years=2).projection) == 2
    comps = [Competitor(name="A", rooms=100, occupancy=0.7, segmentation={"leisure": 0.9})]
    with pytest.raises(ValueError):
        market_study(comps, SubjectHotel(rooms=10, opening_fraction=[1], penetration={"leisure": [1]}), {"leisure": 0}, {"leisure": 100}, 1)


def test_fixvar_hand_calculation_without_inflation():
    r = fixvar_proforma(
        rooms=100, occupancy=[0.7], adr=[110.0], base_occupancy=0.6, base_adr=100.0,
        other_revenues=[RevenueLine(name="fnb", base_amount=1_000_000, fixed_pct=0.4)],
        departmental_expenses=[
            ExpenseLine(name="rooms_expense", base_amount=500_000, fixed_pct=0.6, index="occupancy", department="rooms"),
            ExpenseLine(name="fnb_expense", base_amount=700_000, fixed_pct=0.5, index="department_revenue", department="fnb"),
        ],
        undistributed_expenses=[ExpenseLine(name="a_and_g", base_amount=300_000, fixed_pct=0.7, index="total_revenue")],
        fixed_charges=[ExpenseLine(name="property_tax", base_amount=120_000, fixed_pct=1.0, index="fixed")],
        base_management_fee_pct=0.03, reserve_pct=0.04, inflation=0.0,
    )
    y = r.years[0]
    occ_index = 0.7 / 0.6
    rooms_rev = 100 * 365 * 0.7 * 110
    fnb_rev = 1_000_000 * (0.4 + 0.6 * occ_index)
    total = rooms_rev + fnb_rev
    assert y.revenues["rooms"] == pytest.approx(rooms_rev)
    assert y.revenues["fnb"] == pytest.approx(fnb_rev)
    assert y.departmental_expenses["rooms_expense"] == pytest.approx(500_000 * (0.6 + 0.4 * occ_index))
    assert y.departmental_expenses["fnb_expense"] == pytest.approx(700_000 * (0.5 + 0.5 * fnb_rev / 1_000_000))
    base_total = 100 * 365 * 0.6 * 100 + 1_000_000
    assert y.undistributed_expenses["a_and_g"] == pytest.approx(300_000 * (0.7 + 0.3 * total / base_total))
    assert y.fixed_charges["property_tax"] == pytest.approx(120_000)
    assert y.management_fees == pytest.approx(0.03 * total)
    assert y.reserve_for_replacement == pytest.approx(0.04 * total)
    expected_noi = (total - y.departmental_expenses["rooms_expense"] - y.departmental_expenses["fnb_expense"]
                    - y.undistributed_expenses["a_and_g"] - y.management_fees - 120_000 - 0.04 * total)
    assert y.net_operating_income == pytest.approx(expected_noi)


def test_fixvar_fixed_lines_only_inflate():
    r = fixvar_proforma(
        rooms=50, occupancy=[0.5, 0.8], adr=[100.0, 103.0], base_occupancy=0.65, base_adr=100.0,
        other_revenues=[], departmental_expenses=[], undistributed_expenses=[],
        fixed_charges=[ExpenseLine(name="insurance", base_amount=10_000, fixed_pct=1.0, index="fixed")], inflation=0.03,
    )
    assert r.years[0].fixed_charges["insurance"] == pytest.approx(10_300)
    assert r.years[1].fixed_charges["insurance"] == pytest.approx(10_000 * 1.03**2)
    with pytest.raises(ValueError):
        fixvar_proforma(10, [0.5], [100], 0.6, 100, [], [ExpenseLine(name="x", base_amount=1, fixed_pct=0.5, index="department_revenue", department="spa")], [], [])


def test_mortgage_constant_and_balance():
    f = mortgage_constant(0.06, 25, payments_per_year=1)
    assert f == pytest.approx(0.06 / (1 - 1.06**-25))
    assert loan_balance_fraction(0.06, 25, 0, 1) == pytest.approx(1.0)
    assert loan_balance_fraction(0.06, 25, 25, 1) == 0.0
    # after 10 years the balance equals the PV of the remaining 15 payments
    assert loan_balance_fraction(0.06, 25, 10, 1) == pytest.approx((1 - 1.06**-15) / (1 - 1.06**-25))


def test_mortgage_equity_identity_and_irr():
    noi = [900_000 * 1.03**t for t in range(11)]
    r = mortgage_equity_valuation(noi, equity_yield=0.14, mortgage_interest_rate=0.065, amortization_years=25,
                                  terminal_cap_rate=0.08, loan_to_value=0.6, selling_costs_pct=0.03, rooms=120)
    assert r.binding_constraint == "loan_to_value"
    assert r.loan == pytest.approx(0.6 * r.value)
    # value = loan + PV(equity cash flows) + PV(equity residual) at the equity yield
    pv_eq = sum(cf / 1.14**t for t, cf in enumerate(r.equity_cash_flows, start=1))
    pv_res = r.equity_residual / 1.14**10
    assert r.value == pytest.approx(r.loan + pv_eq + pv_res, rel=1e-9)
    assert r.equity_irr_check == pytest.approx(0.14, abs=1e-6)
    assert r.reversion_net == pytest.approx(noi[10] / 0.08 * 0.97)
    assert r.going_in_cap_rate == pytest.approx(noi[0] / r.value)
    assert r.value_per_key == pytest.approx(r.value / 120)


def test_mortgage_equity_triangulation_takes_most_restrictive_loan():
    noi = [1_000_000] * 11
    r = mortgage_equity_valuation(noi, equity_yield=0.15, mortgage_interest_rate=0.07, amortization_years=25,
                                  terminal_cap_rate=0.085, loan_to_value=0.65, debt_coverage_ratio=1.4, debt_yield=0.10)
    loans = {s.method: s.loan for s in r.sizing}
    assert loans["debt_yield"] == pytest.approx(10_000_000)
    assert loans["debt_coverage_ratio"] == pytest.approx(1_000_000 / (1.4 * r.mortgage_constant))
    assert r.binding_constraint == min(loans, key=loans.get)
    assert r.loan == pytest.approx(min(loans.values()))
    with pytest.raises(ValueError):
        mortgage_equity_valuation(noi, 0.15, 0.07, 25, 0.085)  # no sizing test
    with pytest.raises(ValueError):
        mortgage_equity_valuation(noi[:5], 0.15, 0.07, 25, 0.085, loan_to_value=0.6, holding_period=10)


def test_residual_land_value_bridge():
    r = residual_land_value(stabilised_value=100.0, hard_costs=50.0, soft_costs=10.0, contingency_pct_of_hard=0.0,
                            developer_profit_pct_on_cost=0.15)
    assert r.development_cost_ex_land_ex_finance == pytest.approx(60.0)
    assert r.developer_profit == pytest.approx(9.0)
    assert r.residual_land_value == pytest.approx(31.0)

    r2 = residual_land_value(stabilised_value=100.0, hard_costs=50.0, soft_costs=10.0, contingency_pct_of_hard=0.10,
                             deferral_years=2, discount_rate=0.10, construction_ltc=0.5, construction_interest_rate=0.08,
                             construction_years=2, average_drawn_fraction=0.5, financing_fees_pct=0.01,
                             developer_profit_pct_on_cost=0.15, asking_land_price=30.0)
    dev = 50 + 10 + 5
    loan = 0.5 * dev
    fin = loan * 0.08 * 2 * 0.5 + loan * 0.01
    pv = 100 / 1.1**2
    assert r2.financing_costs == pytest.approx(fin)
    assert r2.residual_land_value == pytest.approx(pv - dev - fin - 0.15 * (dev + fin))
    assert r2.headroom_vs_asking == pytest.approx(r2.residual_land_value - 30.0)
    assert any("asking land price exceeds" in w for w in r2.warnings)


def test_mortgage_equity_sizing_year():
    noi = [500_000, 800_000, 1_000_000] + [1_000_000] * 8
    y1 = mortgage_equity_valuation(noi, 0.15, 0.07, 25, 0.085, debt_yield=0.10)
    y3 = mortgage_equity_valuation(noi, 0.15, 0.07, 25, 0.085, debt_yield=0.10, sizing_year=3)
    assert y1.loan == pytest.approx(5_000_000)
    assert y3.loan == pytest.approx(10_000_000)
    assert y3.sizing_year == 3
    with pytest.raises(ValueError):
        mortgage_equity_valuation(noi, 0.15, 0.07, 25, 0.085, debt_yield=0.10, sizing_year=11)
