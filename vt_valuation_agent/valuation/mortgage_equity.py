"""HMEV: hotel mortgage-equity valuation (simultaneous valuation formula).

Market value is the sum of the mortgage and the present value of the equity
position: the annual net income after debt service over the holding period,
plus the equity residual at reversion (the year n+1 net income capitalised at
the terminal rate, less selling costs, less the outstanding loan balance),
discounted at the equity yield rate.

With the loan sized by loan-to-value the loan depends on the value being
solved for, so the formula is solved in closed form:

    V = (PV(NOI_1..n at y) + R x d_n) / (1 - M + f M a_n + M P_n d_n)

where M is the LTV, f the annual mortgage constant, a_n the annuity factor at
the equity yield y, d_n the single discount factor for year n, P_n the share
of the loan still outstanding after n years and R the net reversion.

Loan sizing is triangulated: the LTV, debt coverage ratio and debt yield
tests each imply a loan and therefore a value; the most restrictive loan is
the one a lender would advance, and the value that goes with it is the
concluded value.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Sequence

from .finance_math import irr


@dataclass
class LoanSizing:
    method: str
    loan: float
    value: float
    implied_ltv: float
    implied_dcr: float
    implied_debt_yield: float
    annual_debt_service: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MortgageEquityResult:
    holding_period: int
    sizing_year: int
    equity_yield: float
    mortgage_interest_rate: float
    amortization_years: int
    mortgage_constant: float
    terminal_cap_rate: float
    selling_costs_pct: float
    sizing: list[LoanSizing]
    binding_constraint: str
    value: float
    loan: float
    equity: float
    annual_debt_service: float
    equity_cash_flows: list[float]
    reversion_gross: float
    reversion_net: float
    loan_balance_at_reversion: float
    equity_residual: float
    going_in_cap_rate: float
    equity_irr_check: float
    value_per_key: float | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["sizing"] = [s.to_dict() for s in self.sizing]
        return d


def mortgage_constant(interest_rate: float, amortization_years: int, payments_per_year: int = 12) -> float:
    """Annual debt service per unit of loan for a fully amortising mortgage."""
    if amortization_years <= 0:
        raise ValueError("amortization_years must be positive")
    if interest_rate < 0:
        raise ValueError("interest_rate cannot be negative")
    m = payments_per_year
    n = amortization_years * m
    if interest_rate == 0:
        return 1.0 / amortization_years
    r = interest_rate / m
    return m * r / (1.0 - (1.0 + r) ** (-n))


def loan_balance_fraction(interest_rate: float, amortization_years: int, years_elapsed: int, payments_per_year: int = 12) -> float:
    """Share of the original loan still outstanding after ``years_elapsed``."""
    if years_elapsed >= amortization_years:
        return 0.0
    if interest_rate == 0:
        return 1.0 - years_elapsed / amortization_years
    m = payments_per_year
    r = interest_rate / m
    total, remaining = amortization_years * m, (amortization_years - years_elapsed) * m
    return (1.0 - (1.0 + r) ** (-remaining)) / (1.0 - (1.0 + r) ** (-total))


def mortgage_equity_valuation(
    net_income: Sequence[float],
    equity_yield: float,
    mortgage_interest_rate: float,
    amortization_years: int,
    terminal_cap_rate: float,
    loan_to_value: float | None = None,
    debt_coverage_ratio: float | None = None,
    debt_yield: float | None = None,
    selling_costs_pct: float = 0.03,
    holding_period: int | None = None,
    rooms: int | None = None,
    payments_per_year: int = 12,
    sizing_year: int = 1,
) -> MortgageEquityResult:
    """Value a hotel with the mortgage-equity technique.

    ``net_income`` must hold the holding period plus one year (the extra year
    is capitalised for the reversion). At least one of ``loan_to_value``,
    ``debt_coverage_ratio`` and ``debt_yield`` must be given. The DCR and
    debt-yield tests use the net income of ``sizing_year`` (1 by default;
    lenders often size on the first stabilised year instead).
    """
    noi = [float(x) for x in net_income]
    n = holding_period if holding_period is not None else len(noi) - 1
    if n < 1 or len(noi) < n + 1:
        raise ValueError("net_income needs holding_period + 1 years (the last year is capitalised for the reversion)")
    if equity_yield <= 0:
        raise ValueError("equity_yield must be positive")
    if terminal_cap_rate <= 0:
        raise ValueError("terminal_cap_rate must be positive")
    if not 0 <= selling_costs_pct < 1:
        raise ValueError("selling_costs_pct must be between 0 and 1")
    if loan_to_value is None and debt_coverage_ratio is None and debt_yield is None:
        raise ValueError("provide at least one of loan_to_value, debt_coverage_ratio or debt_yield")
    if loan_to_value is not None and not 0 <= loan_to_value < 1:
        raise ValueError("loan_to_value must be between 0 and 1")
    if not 1 <= sizing_year <= n:
        raise ValueError("sizing_year must be within the holding period")
    noi_size = noi[sizing_year - 1]

    f = mortgage_constant(mortgage_interest_rate, amortization_years, payments_per_year)
    P_n = loan_balance_fraction(mortgage_interest_rate, amortization_years, n, payments_per_year)
    y = equity_yield
    disc = [1.0 / (1.0 + y) ** t for t in range(1, n + 1)]
    a_n = sum(disc)
    d_n = disc[-1]
    pv_noi = sum(noi[t] * disc[t] for t in range(n))
    reversion_gross = noi[n] / terminal_cap_rate
    reversion_net = reversion_gross * (1.0 - selling_costs_pct)
    warnings: list[str] = []

    def value_for_loan(loan: float) -> float:
        return loan + pv_noi - f * loan * a_n + (reversion_net - loan * P_n) * d_n

    sizing: list[LoanSizing] = []
    if loan_to_value is not None:
        M = loan_to_value
        denom = 1.0 - M + f * M * a_n + M * P_n * d_n
        v = (pv_noi + reversion_net * d_n) / denom
        sizing.append(_sizing("loan_to_value", M * v, v, f, noi_size))
    if debt_coverage_ratio is not None:
        if debt_coverage_ratio <= 0:
            raise ValueError("debt_coverage_ratio must be positive")
        loan = noi_size / (debt_coverage_ratio * f)
        sizing.append(_sizing("debt_coverage_ratio", loan, value_for_loan(loan), f, noi_size))
    if debt_yield is not None:
        if debt_yield <= 0:
            raise ValueError("debt_yield must be positive")
        loan = noi_size / debt_yield
        sizing.append(_sizing("debt_yield", loan, value_for_loan(loan), f, noi_size))

    binding = min(sizing, key=lambda s: s.loan)
    loan, value = binding.loan, binding.value
    if value <= 0:
        raise ValueError("the inputs produce a non-positive value; check the net income and yield assumptions")
    ds = f * loan
    equity = value - loan
    eq_cfs = [noi[t] - ds for t in range(n)]
    balance = loan * P_n
    residual = reversion_net - balance
    going_in = noi[0] / value
    try:
        irr_check = irr([-equity] + eq_cfs[:-1] + [eq_cfs[-1] + residual])
    except ValueError:
        irr_check = float("nan")
        warnings.append("equity cash flows do not support an IRR; the equity position may be negative in most years")
    if any(cf < 0 for cf in eq_cfs):
        warnings.append("net income does not cover debt service in at least one year; the lender's DCR covenant may be breached during ramp-up")
    if terminal_cap_rate <= going_in:
        warnings.append("terminal cap rate at or below the going-in cap rate assumes the asset gets less risky over the hold; justify or raise it")
    if loan_to_value is not None and binding.method != "loan_to_value":
        warnings.append(f"the {binding.method.replace('_', ' ')} test, not LTV, limits the loan: implied LTV {binding.implied_ltv:.1%}")
    return MortgageEquityResult(
        holding_period=n, sizing_year=sizing_year, equity_yield=y, mortgage_interest_rate=mortgage_interest_rate, amortization_years=amortization_years,
        mortgage_constant=f, terminal_cap_rate=terminal_cap_rate, selling_costs_pct=selling_costs_pct, sizing=sizing,
        binding_constraint=binding.method, value=value, loan=loan, equity=equity, annual_debt_service=ds,
        equity_cash_flows=eq_cfs, reversion_gross=reversion_gross, reversion_net=reversion_net,
        loan_balance_at_reversion=balance, equity_residual=residual, going_in_cap_rate=going_in,
        equity_irr_check=irr_check, value_per_key=(value / rooms) if rooms else None, warnings=warnings,
    )


def _sizing(method: str, loan: float, value: float, f: float, noi_1: float) -> LoanSizing:
    ds = f * loan
    return LoanSizing(
        method=method, loan=loan, value=value,
        implied_ltv=(loan / value) if value else 0.0,
        implied_dcr=(noi_1 / ds) if ds else float("inf"),
        implied_debt_yield=(noi_1 / loan) if loan else float("inf"),
        annual_debt_service=ds,
    )
