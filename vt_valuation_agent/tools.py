"""Claude tool definitions wrapping the deterministic valuation engine.

Every tool returns a JSON string so the model can quote exact figures, and
raises ``ToolError`` on invalid inputs so the model sees a clear, correctable
error instead of a stack trace. Inputs are validated against the generated
schema by the SDK before a function runs.
"""

from __future__ import annotations

import json
from typing import Optional

from anthropic import beta_tool
from anthropic.lib.tools import ToolError

# Import from the submodules directly: the package re-exports functions named
# ``wacc`` and ``football_field`` that would otherwise shadow the modules.
from .valuation import finance_math
from .valuation.comps import Comparable, TargetMetrics, relative_valuation
from .valuation.dcf import dcf_valuation as _dcf_valuation
from .valuation.dcf import project_free_cash_flows as _project_free_cash_flows
from .valuation.football_field import ValuationRange, football_field as _football_field
from .valuation.hotel_fixvar import ExpenseLine, RevenueLine, fixvar_proforma as _fixvar_proforma
from .valuation.hotel_market import Competitor, NewSupply, SubjectHotel, market_study as _market_study
from .valuation.mortgage_equity import mortgage_equity_valuation as _mortgage_equity_valuation
from .valuation.residual import residual_land_value as _residual_land_value
from .valuation.lbo import lbo_returns as _lbo_returns
from .valuation.lbo import max_entry_multiple_for_irr as _max_entry_multiple_for_irr
from .valuation.sensitivity import dcf_sensitivity as _dcf_sensitivity
from .valuation.wacc import cost_of_equity_capm, relever_beta, unlever_beta, wacc as _wacc


def _dump(obj) -> str:
    return json.dumps(_round(obj), indent=None, sort_keys=False)


def _round(obj, places: int = 6):
    if isinstance(obj, float):
        return round(obj, places)
    if isinstance(obj, dict):
        return {k: _round(v, places) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v, places) for v in obj]
    return obj


def _guard(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except (ValueError, ZeroDivisionError) as exc:
        raise ToolError(f"Invalid inputs: {exc}") from exc


@beta_tool(eager_input_streaming=True)
def compute_wacc(
    risk_free_rate: float,
    beta: float,
    equity_risk_premium: float,
    pre_tax_cost_of_debt: float,
    tax_rate: float,
    debt_weight: Optional[float] = None,
    equity_value: Optional[float] = None,
    debt_value: Optional[float] = None,
    size_premium: float = 0.0,
    country_risk_premium: float = 0.0,
    company_specific_premium: float = 0.0,
) -> str:
    """Compute the cost of equity (CAPM plus optional premia) and the WACC.

    Call this before any DCF so the discount rate is derived transparently from
    its components rather than asserted. All rates are decimals (0.045 = 4.5%).

    Args:
        risk_free_rate: Risk-free rate, e.g. the 10-year government bond yield.
        beta: Levered equity beta of the target.
        equity_risk_premium: Market equity risk premium.
        pre_tax_cost_of_debt: Pre-tax cost of debt (yield on the company's debt).
        tax_rate: Marginal corporate tax rate.
        debt_weight: Target debt / (debt + equity). Provide this OR market values.
        equity_value: Market value of equity, used with debt_value to derive weights.
        debt_value: Market value of debt, used with equity_value to derive weights.
        size_premium: Optional small-cap premium added to the cost of equity.
        country_risk_premium: Optional country risk premium added to the cost of equity.
        company_specific_premium: Optional company-specific risk premium.
    """
    ke = cost_of_equity_capm(
        risk_free_rate, beta, equity_risk_premium, size_premium, country_risk_premium, company_specific_premium
    )
    result = _guard(
        _wacc,
        cost_of_equity=ke,
        pre_tax_cost_of_debt=pre_tax_cost_of_debt,
        tax_rate=tax_rate,
        equity_value=equity_value,
        debt_value=debt_value,
        debt_weight=debt_weight,
    )
    out = result.to_dict()
    out["inputs"] = {
        "risk_free_rate": risk_free_rate,
        "beta": beta,
        "equity_risk_premium": equity_risk_premium,
        "size_premium": size_premium,
        "country_risk_premium": country_risk_premium,
        "company_specific_premium": company_specific_premium,
    }
    return _dump(out)


@beta_tool(eager_input_streaming=True)
def lever_beta(
    beta: float,
    debt_to_equity: float,
    tax_rate: float,
    direction: str = "relever",
) -> str:
    """Unlever or relever an equity beta with the Hamada formula.

    Use this to move peer betas to an unlevered basis and relever them at the
    target's capital structure. Args:
        beta: The input beta (levered if unlevering, unlevered if relevering).
        debt_to_equity: Debt / equity ratio to use.
        tax_rate: Marginal tax rate as a decimal.
        direction: "unlever" or "relever".
    """
    if direction not in ("unlever", "relever"):
        raise ToolError("direction must be 'unlever' or 'relever'")
    fn = unlever_beta if direction == "unlever" else relever_beta
    value = _guard(fn, beta, debt_to_equity, tax_rate)
    return _dump({"direction": direction, "input_beta": beta, "debt_to_equity": debt_to_equity, "tax_rate": tax_rate, "output_beta": value})


@beta_tool(eager_input_streaming=True)
def project_free_cash_flows(
    base_revenue: float,
    revenue_growth: list[float],
    ebitda_margin: list[float],
    da_pct_revenue: float,
    capex_pct_revenue: float,
    nwc_pct_revenue: float,
    tax_rate: float,
    base_nwc: Optional[float] = None,
) -> str:
    """Build an explicit-period unlevered free cash flow schedule from operating assumptions.

    Call this when you have revenue, margin and reinvestment assumptions but not
    a ready-made FCF series. Returns revenue, EBITDA, EBIT, taxes, capex, change
    in working capital and unlevered FCF for each year.

    Args:
        base_revenue: Last actual (year 0) revenue.
        revenue_growth: Growth rate per projection year, e.g. [0.10, 0.08, 0.06, 0.05, 0.04].
        ebitda_margin: EBITDA margin per projection year (same length as revenue_growth); repeat a value for a flat margin.
        da_pct_revenue: Depreciation and amortisation as a share of revenue.
        capex_pct_revenue: Capital expenditure as a share of revenue.
        nwc_pct_revenue: Net working capital as a share of revenue; the cash impact is the year-on-year change.
        tax_rate: Cash tax rate on EBIT.
        base_nwc: Year 0 net working capital; defaults to nwc_pct_revenue times base_revenue.
    """
    schedule = _guard(
        _project_free_cash_flows,
        base_revenue, revenue_growth, ebitda_margin, da_pct_revenue, capex_pct_revenue, nwc_pct_revenue, tax_rate, base_nwc,
    )
    return _dump({"years": [y.to_dict() for y in schedule], "unlevered_fcf": [y.unlevered_fcf for y in schedule], "final_year_ebitda": schedule[-1].ebitda})


@beta_tool(eager_input_streaming=True)
def dcf_valuation(
    free_cash_flows: list[float],
    discount_rate: float,
    terminal_growth: Optional[float] = None,
    exit_multiple: Optional[float] = None,
    terminal_metric: Optional[float] = None,
    mid_year: bool = True,
    net_debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_stock: float = 0.0,
    non_operating_assets: float = 0.0,
    shares_outstanding: Optional[float] = None,
) -> str:
    """Discount unlevered free cash flows to enterprise value, equity value and value per share.

    Use this for every DCF figure you report; never compute present values by
    hand. Provide exactly one terminal method: terminal_growth (perpetuity) or
    exit_multiple with terminal_metric (e.g. final-year EBITDA). Passing
    terminal_metric alongside terminal_growth also returns the implied exit
    multiple, which is a useful sanity check against comps.

    Args:
        free_cash_flows: Unlevered FCF for years 1..n in consistent units.
        discount_rate: WACC as a decimal.
        terminal_growth: Perpetual growth rate for the Gordon growth terminal value.
        exit_multiple: Terminal multiple applied to terminal_metric.
        terminal_metric: Final-year metric (usually EBITDA) the exit multiple applies to.
        mid_year: Use the mid-year discounting convention (default true).
        net_debt: Debt minus cash at the valuation date.
        minority_interest: Non-controlling interests to subtract.
        preferred_stock: Preferred equity to subtract.
        non_operating_assets: Investments or excess assets to add.
        shares_outstanding: Fully diluted shares, to express value per share.
    """
    result = _guard(
        _dcf_valuation,
        free_cash_flows, discount_rate, terminal_growth, exit_multiple, terminal_metric, mid_year,
        net_debt, minority_interest, preferred_stock, non_operating_assets, shares_outstanding,
    )
    return _dump(result.to_dict())


@beta_tool(eager_input_streaming=True)
def dcf_sensitivity(
    free_cash_flows: list[float],
    discount_rates: list[float],
    terminal_growth_rates: Optional[list[float]] = None,
    exit_multiples: Optional[list[float]] = None,
    terminal_metric: Optional[float] = None,
    output: str = "enterprise_value",
    mid_year: bool = True,
    net_debt: float = 0.0,
    shares_outstanding: Optional[float] = None,
) -> str:
    """Two-way DCF sensitivity table: discount rate (rows) against terminal growth or exit multiple (columns).

    Call this after a base-case DCF to show how the value moves with the two
    assumptions that matter most. Returns the grid as JSON and as a markdown table.

    Args:
        free_cash_flows: Unlevered FCF for years 1..n.
        discount_rates: Row values, e.g. [0.08, 0.09, 0.10, 0.11, 0.12].
        terminal_growth_rates: Column values for the perpetuity method.
        exit_multiples: Column values for the exit-multiple method (requires terminal_metric).
        terminal_metric: Final-year metric for the exit-multiple method.
        output: Field to tabulate: enterprise_value, equity_value or value_per_share.
        mid_year: Use the mid-year convention.
        net_debt: Net debt for the equity bridge.
        shares_outstanding: Shares for per-share output.
    """
    if output not in ("enterprise_value", "equity_value", "value_per_share"):
        raise ToolError("output must be enterprise_value, equity_value or value_per_share")
    table = _guard(
        _dcf_sensitivity,
        free_cash_flows, discount_rates, terminal_growth_rates, exit_multiples, terminal_metric, output,
        mid_year=mid_year, net_debt=net_debt, shares_outstanding=shares_outstanding,
    )
    out = table.to_dict()
    out["markdown"] = table.to_markdown("{:,.2f}" if output == "value_per_share" else "{:,.1f}")
    return _dump(out)


@beta_tool(eager_input_streaming=True)
def trading_comps(
    peers: list[Comparable],
    target: TargetMetrics,
    net_debt: float = 0.0,
    shares_outstanding: Optional[float] = None,
) -> str:
    """Trading comparables: peer multiple statistics and the implied valuation range for the target.

    Call this whenever peer multiples are available. Supports EV/Revenue,
    EV/EBITDA, EV/EBIT and P/E; leave a multiple null when it is not known.
    Implied values are given at the peer first quartile (low), median (mid)
    and third quartile (high).

    Args:
        peers: Comparable public companies with their current multiples.
        target: The target's revenue, EBITDA, EBIT and net income (same units as the peers' denominators).
        net_debt: Target net debt for the EV-to-equity bridge.
        shares_outstanding: Target diluted shares for per-share values.
    """
    result = _guard(relative_valuation, peers, target, net_debt, shares_outstanding, "trading_comps")
    return _dump(result.to_dict())


@beta_tool(eager_input_streaming=True)
def precedent_transactions(
    deals: list[Comparable],
    target: TargetMetrics,
    net_debt: float = 0.0,
    shares_outstanding: Optional[float] = None,
) -> str:
    """Precedent transactions: deal multiple statistics and the implied control-basis valuation of the target.

    Use for M&A or take-private contexts. Same mechanics as trading comps; the
    result notes that transaction multiples embed a control premium.

    Args:
        deals: Past transactions with their EV/Revenue, EV/EBITDA, EV/EBIT or P/E multiples.
        target: The target's metrics the multiples are applied to.
        net_debt: Target net debt for the EV-to-equity bridge.
        shares_outstanding: Target diluted shares for per-share values.
    """
    result = _guard(relative_valuation, deals, target, net_debt, shares_outstanding, "precedent_transactions")
    return _dump(result.to_dict())


@beta_tool(eager_input_streaming=True)
def lbo_returns(
    entry_ebitda: float,
    entry_multiple: float,
    exit_multiple: float,
    ebitda_growth: list[float],
    leverage_multiple: float,
    interest_rate: float,
    tax_rate: float,
    da_pct_ebitda: float = 0.0,
    capex_pct_ebitda: float = 0.0,
    nwc_pct_ebitda_change: float = 0.0,
    cash_sweep: float = 1.0,
    fees_pct_ev: float = 0.02,
) -> str:
    """Sponsor returns (MOIC and IRR) for a simple leveraged buyout, with the annual debt paydown schedule.

    Use this to test what a financial buyer could pay, or to cross-check a
    valuation against a required return. One EBITDA growth rate per hold year.

    Args:
        entry_ebitda: LTM EBITDA at entry.
        entry_multiple: Entry EV / EBITDA.
        exit_multiple: Exit EV / EBITDA.
        ebitda_growth: EBITDA growth per hold year, e.g. [0.08, 0.07, 0.06, 0.05, 0.05].
        leverage_multiple: Entry debt / EBITDA.
        interest_rate: Blended cash interest rate on the debt.
        tax_rate: Cash tax rate.
        da_pct_ebitda: D&A as a share of EBITDA (tax shield).
        capex_pct_ebitda: Capex as a share of EBITDA.
        nwc_pct_ebitda_change: Working capital investment per unit of EBITDA growth.
        cash_sweep: Share of free cash flow used to repay debt (0 to 1).
        fees_pct_ev: Transaction fees as a share of entry EV, funded by equity.
    """
    result = _guard(
        _lbo_returns,
        entry_ebitda, entry_multiple, exit_multiple, ebitda_growth, leverage_multiple, interest_rate, tax_rate,
        da_pct_ebitda, capex_pct_ebitda, nwc_pct_ebitda_change, cash_sweep, fees_pct_ev,
    )
    return _dump(result.to_dict())


@beta_tool(eager_input_streaming=True)
def max_entry_multiple_for_target_irr(
    target_irr: float,
    entry_ebitda: float,
    exit_multiple: float,
    ebitda_growth: list[float],
    leverage_multiple: float,
    interest_rate: float,
    tax_rate: float,
    da_pct_ebitda: float = 0.0,
    capex_pct_ebitda: float = 0.0,
    nwc_pct_ebitda_change: float = 0.0,
    cash_sweep: float = 1.0,
    fees_pct_ev: float = 0.02,
) -> str:
    """Solve for the highest entry EV/EBITDA multiple at which a sponsor still earns the target IRR.

    Use this to express an LBO 'ability to pay' as a valuation range. Args mirror
    lbo_returns, minus entry_multiple.

    Args:
        target_irr: Required IRR as a decimal, e.g. 0.20.
        entry_ebitda: LTM EBITDA at entry.
        exit_multiple: Exit EV / EBITDA.
        ebitda_growth: EBITDA growth per hold year.
        leverage_multiple: Entry debt / EBITDA.
        interest_rate: Blended cash interest rate.
        tax_rate: Cash tax rate.
        da_pct_ebitda: D&A as a share of EBITDA.
        capex_pct_ebitda: Capex as a share of EBITDA.
        nwc_pct_ebitda_change: Working capital investment per unit of EBITDA growth.
        cash_sweep: Share of free cash flow used to repay debt.
        fees_pct_ev: Transaction fees as a share of entry EV.
    """
    kwargs = dict(
        entry_ebitda=entry_ebitda, exit_multiple=exit_multiple, ebitda_growth=ebitda_growth,
        leverage_multiple=leverage_multiple, interest_rate=interest_rate, tax_rate=tax_rate,
        da_pct_ebitda=da_pct_ebitda, capex_pct_ebitda=capex_pct_ebitda,
        nwc_pct_ebitda_change=nwc_pct_ebitda_change, cash_sweep=cash_sweep, fees_pct_ev=fees_pct_ev,
    )
    multiple = _guard(_max_entry_multiple_for_irr, target_irr, **kwargs)
    detail = _lbo_returns(entry_multiple=multiple, **kwargs)
    return _dump({"target_irr": target_irr, "max_entry_multiple": multiple, "implied_entry_enterprise_value": detail.entry_enterprise_value, "moic_at_max": detail.moic})


@beta_tool(eager_input_streaming=True)
def build_football_field(
    ranges: list[ValuationRange],
    net_debt: float = 0.0,
    shares_outstanding: Optional[float] = None,
) -> str:
    """Combine valuation ranges from different methods into a football field with a blended value.

    Call this last, once you have a low/high from each method (DCF cases, comps
    quartiles, precedents, LBO ability-to-pay, 52-week range). Every range is
    normalised to enterprise, equity and per-share terms.

    Args:
        ranges: One entry per method with low, high, optional mid, basis and weight.
        net_debt: Net debt for the enterprise-to-equity bridge.
        shares_outstanding: Diluted shares for per-share values.
    """
    result = _guard(_football_field, ranges, net_debt, shares_outstanding)
    return _dump(result.to_dict())


@beta_tool(eager_input_streaming=True)
def financial_calculator(
    operation: str,
    cash_flows: list[float],
    rate: Optional[float] = None,
    mid_year: bool = False,
) -> str:
    """Small financial calculator for NPV, IRR and CAGR on an arbitrary cash flow series.

    Use this for one-off arithmetic that the other tools do not cover, instead
    of computing by hand.

    Args:
        operation: "npv" (flows in periods 1..n, needs rate), "irr" (flows in periods 0..n), or "cagr" (uses first and last values and the number of periods between them).
        cash_flows: The cash flow or value series.
        rate: Discount rate for npv.
        mid_year: Mid-year convention for npv.
    """
    if operation == "npv":
        if rate is None:
            raise ToolError("npv requires rate")
        value = _guard(finance_math.npv, rate, cash_flows, mid_year)
    elif operation == "irr":
        value = _guard(finance_math.irr, cash_flows)
    elif operation == "cagr":
        if len(cash_flows) < 2:
            raise ToolError("cagr needs at least two values")
        value = _guard(finance_math.cagr, cash_flows[0], cash_flows[-1], len(cash_flows) - 1)
    else:
        raise ToolError("operation must be npv, irr or cagr")
    return _dump({"operation": operation, "result": value})


@beta_tool(eager_input_streaming=True)
def hotel_market_study(
    competitors: list[Competitor],
    subject: SubjectHotel,
    segment_growth: dict[str, float],
    base_segment_adr: dict[str, float],
    years: int,
    unaccommodated_demand: Optional[dict[str, float]] = None,
    induced_demand: Optional[dict[str, list[float]]] = None,
    new_supply: Optional[list[NewSupply]] = None,
    adr_inflation: float = 0.03,
    max_occupancy: Optional[float] = None,
) -> str:
    """RNAADR: built-up room-night analysis and ADR forecast for a proposed hotel (HVS method).

    Call this first for any hotel project. From the competitive set it derives
    base-year accommodated demand by segment, each competitor's fair share,
    market share and penetration index, then projects market demand (with
    unaccommodated and induced demand and segment growth), new supply, and the
    subject's room nights, occupancy, segment ADRs, blended ADR and RevPAR by
    year. Feed occupancy_by_year and adr_by_year into hotel_fixvar_proforma.

    Args:
        competitors: Existing competitive hotels with rooms, base-year occupancy, segmentation, fraction open and competitive weight.
        subject: The proposed hotel: rooms, opening fraction per year, penetration index per segment per year, ADR index per segment, optional ADR ramp.
        segment_growth: Annual demand growth per segment, e.g. {"leisure": 0.03, "meeting": 0.02}.
        base_segment_adr: Market ADR per segment in base-year currency, e.g. {"leisure": 320, "meeting": 260}.
        years: Number of projection years (10 for the HVS convention).
        unaccommodated_demand: Latent demand per segment as a share of base-year accommodated room nights, e.g. {"leisure": 0.05}.
        induced_demand: Room nights per segment per year created by a new demand generator.
        new_supply: Competitive hotels opening during the projection period.
        adr_inflation: Annual ADR inflation applied to market segment ADRs.
        max_occupancy: Optional cap on the subject's occupancy.
    """
    result = _guard(
        _market_study, competitors, subject, segment_growth, base_segment_adr, years,
        unaccommodated_demand, induced_demand, new_supply, adr_inflation, max_occupancy,
    )
    return _dump(result.to_dict())


@beta_tool(eager_input_streaming=True)
def hotel_fixvar_proforma(
    rooms: int,
    occupancy: list[float],
    adr: list[float],
    base_occupancy: float,
    base_adr: float,
    other_revenues: list[RevenueLine],
    departmental_expenses: list[ExpenseLine],
    undistributed_expenses: list[ExpenseLine],
    fixed_charges: list[ExpenseLine],
    base_management_fee_pct: float = 0.03,
    incentive_fee_pct_of_gop: float = 0.0,
    reserve_pct: float = 0.04,
    inflation: float = 0.03,
    available_rooms_fraction: Optional[list[float]] = None,
) -> str:
    """FIXVAR: fixed and variable component forecast of the hotel operating statement (HVS method).

    Call this after hotel_market_study with its occupancy and ADR series. Each
    line is projected as base x inflation x (fixed share + variable share x
    index ratio), where the index is occupancy, the department's own revenue
    or total revenue. Returns a USALI-style statement per year down to net
    operating income after management fees, fixed charges and the reserve;
    noi_by_year feeds hotel_mortgage_equity_valuation.

    Args:
        rooms: Room count.
        occupancy: Projected occupancy per year.
        adr: Projected nominal ADR per year.
        base_occupancy: Occupancy at which the base statement is stated.
        base_adr: Base-year ADR in current currency.
        other_revenues: Non-rooms revenue departments with base amount and fixed share (index is occupancy).
        departmental_expenses: Departmental expenses; rooms expense uses index "occupancy" with department "rooms", others "department_revenue".
        undistributed_expenses: A&G, marketing, property operations, utilities; index usually "total_revenue".
        fixed_charges: Property tax, insurance and similar; index usually "fixed".
        base_management_fee_pct: Base management fee as a share of total revenue.
        incentive_fee_pct_of_gop: Incentive fee as a share of GOP.
        reserve_pct: Reserve for replacement as a share of total revenue (HVS convention 4 percent).
        inflation: Annual inflation applied to all lines.
        available_rooms_fraction: Share of the year rooms are available, for a partial opening year.
    """
    result = _guard(
        _fixvar_proforma, rooms, occupancy, adr, base_occupancy, base_adr, other_revenues, departmental_expenses,
        undistributed_expenses, fixed_charges, base_management_fee_pct, incentive_fee_pct_of_gop, reserve_pct, inflation,
        available_rooms_fraction,
    )
    return _dump(result.to_dict())


@beta_tool(eager_input_streaming=True)
def hotel_mortgage_equity_valuation(
    net_income: list[float],
    equity_yield: float,
    mortgage_interest_rate: float,
    amortization_years: int,
    terminal_cap_rate: float,
    loan_to_value: Optional[float] = None,
    debt_coverage_ratio: Optional[float] = None,
    debt_yield: Optional[float] = None,
    selling_costs_pct: float = 0.03,
    holding_period: Optional[int] = None,
    rooms: Optional[int] = None,
    sizing_year: int = 1,
) -> str:
    """HMEV: hotel mortgage-equity valuation with loan sizing triangulated on LTV, DCR and debt yield (HVS method).

    Call this with the FIXVAR net operating income for the holding period plus
    one year. Solves the simultaneous valuation formula: value equals the
    mortgage plus the present value, at the equity yield, of net income after
    debt service and the equity residual (year n+1 income capitalised at the
    terminal rate less selling costs less the loan balance). The most
    restrictive loan test governs the concluded value.

    Args:
        net_income: NOI for years 1..n+1 (the last year is capitalised for the reversion).
        equity_yield: Required before-tax equity yield rate, e.g. 0.16.
        mortgage_interest_rate: Mortgage interest rate.
        amortization_years: Amortisation period in years.
        terminal_cap_rate: Terminal capitalisation rate applied to year n+1 income.
        loan_to_value: Lender LTV limit, e.g. 0.60.
        debt_coverage_ratio: Lender minimum DCR on year-1 income, e.g. 1.35.
        debt_yield: Lender minimum debt yield on year-1 income, e.g. 0.10.
        selling_costs_pct: Brokerage and legal costs at reversion.
        holding_period: Years held; defaults to len(net_income) - 1.
        rooms: Room count, to report value per key.
        sizing_year: Projection year whose NOI the DCR and debt-yield tests use (1 by default; use the first stabilised year when the lender sizes on stabilised income).
    """
    result = _guard(
        _mortgage_equity_valuation, net_income, equity_yield, mortgage_interest_rate, amortization_years, terminal_cap_rate,
        loan_to_value, debt_coverage_ratio, debt_yield, selling_costs_pct, holding_period, rooms, 12, sizing_year,
    )
    return _dump(result.to_dict())


@beta_tool(eager_input_streaming=True)
def residual_land_value(
    stabilised_value: float,
    hard_costs: float,
    soft_costs: float,
    ffe_ose: float = 0.0,
    site_works: float = 0.0,
    preopening_working_capital: float = 0.0,
    contingency_pct_of_hard: float = 0.075,
    deferral_years: float = 0.0,
    discount_rate: float = 0.0,
    construction_ltc: float = 0.0,
    construction_interest_rate: float = 0.0,
    construction_years: float = 0.0,
    average_drawn_fraction: float = 0.55,
    financing_fees_pct: float = 0.01,
    developer_profit_pct_on_cost: float = 0.15,
    land_transaction_costs_pct: float = 0.0,
    asking_land_price: Optional[float] = None,
) -> str:
    """Residual land value for a greenfield hotel or resort: stabilised value less all development, financing and profit requirements.

    Call this last with the mortgage-equity (or DCF) value at stabilisation.
    The value is deferred to today over the construction and ramp-up period,
    then hard, site, soft, FF&E, pre-opening, contingency, construction
    financing and developer profit are deducted. Reports the maximum land bid
    and, if an asking price is given, the headroom and profit on cost at that price.

    Args:
        stabilised_value: Property value when stabilised (same currency as costs).
        hard_costs: Building construction costs.
        soft_costs: Design, permits, fees, marketing, technical services.
        ffe_ose: Furniture, fixtures, equipment and operating supplies.
        site_works: Earthworks, infrastructure, landscaping.
        preopening_working_capital: Pre-opening expenses and opening working capital.
        contingency_pct_of_hard: Contingency as a share of hard and site costs.
        deferral_years: Years from today until stabilisation.
        discount_rate: Rate used to defer the stabilised value to today.
        construction_ltc: Construction loan as a share of development cost excluding land.
        construction_interest_rate: Construction loan interest rate.
        construction_years: Construction period in years.
        average_drawn_fraction: Average drawn share of the construction loan over the period.
        financing_fees_pct: Arrangement fees as a share of the loan.
        developer_profit_pct_on_cost: Required developer profit on cost including finance.
        land_transaction_costs_pct: Transfer tax and fees on the land, to net the bid.
        asking_land_price: Vendor's asking price, to report headroom.
    """
    result = _guard(
        _residual_land_value, stabilised_value, hard_costs, soft_costs, ffe_ose, site_works, preopening_working_capital,
        contingency_pct_of_hard, deferral_years, discount_rate, construction_ltc, construction_interest_rate, construction_years,
        average_drawn_fraction, financing_fees_pct, developer_profit_pct_on_cost, land_transaction_costs_pct, asking_land_price,
    )
    return _dump(result.to_dict())


VALUATION_TOOLS = [
    compute_wacc,
    lever_beta,
    project_free_cash_flows,
    dcf_valuation,
    dcf_sensitivity,
    trading_comps,
    precedent_transactions,
    lbo_returns,
    max_entry_multiple_for_target_irr,
    build_football_field,
    financial_calculator,
    hotel_market_study,
    hotel_fixvar_proforma,
    hotel_mortgage_equity_valuation,
    residual_land_value,
]
