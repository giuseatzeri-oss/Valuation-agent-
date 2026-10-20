"""Development cash flow, project and equity returns, and the discounted
residual land value.

Annual periods, year 0 being acquisition. Costs are spread over their
duration on a straight line or an S-curve. A construction loan funds a share
of development cost (not land); interest accrues on the opening balance and is
capitalised until the asset opens, paid from operating cash afterwards, and
the balance is repaid at exit from the net sale proceeds. Equity funds
everything the loan does not.

The discounted residual land value is the land payment at year 0 that makes
the unlevered project IRR equal to the required project return, with every
other flow held fixed.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Literal, Optional, Sequence

from pydantic import BaseModel, Field

from .finance_math import irr


class CostItem(BaseModel):
    name: str
    amount: float = Field(ge=0, description="Total cost in today's currency (escalate before entering if required)")
    start_year: int = Field(ge=0, description="First year of spend (0 = acquisition year)")
    duration_years: int = Field(default=1, ge=1)
    profile: Literal["straight", "s_curve"] = Field(default="s_curve")


@dataclass
class DevelopmentYear:
    year: int
    land: float
    development_costs: float
    operating_noi: float
    residential_net_receipts: float
    other_income: float
    exit_proceeds_gross: float
    unlevered_cash_flow: float
    loan_draw: float
    interest_accrued: float
    interest_capitalised: float
    interest_paid: float
    principal_repaid: float
    loan_balance_end: float
    equity_cash_flow: float
    cumulative_equity: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DevelopmentResult:
    years: list[DevelopmentYear]
    total_development_cost: float
    total_investment_incl_land_and_finance: float
    peak_equity: float
    peak_debt: float
    exit_year: int
    exit_value: float
    exit_net_proceeds: float
    unlevered_irr: float
    unlevered_npv_at_hurdle: float
    project_profit_on_cost: float
    equity_irr: float | None
    equity_multiple: float | None
    equity_payback_year: int | None
    discounted_residual_land_value: float | None
    unlevered_cash_flows: list[float]
    equity_cash_flows: list[float]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["years"] = [y.to_dict() for y in self.years]
        return d


def development_cash_flow(
    land_cost: float,
    cost_items: list[CostItem],
    operating_noi: Sequence[float],
    exit_year: int,
    terminal_cap_rate: float,
    exit_noi: float,
    project_hurdle_rate: float,
    residential_net_receipts: Optional[Sequence[float]] = None,
    other_income: Optional[Sequence[float]] = None,
    selling_costs_pct: float = 0.02,
    opening_year: Optional[int] = None,
    construction_ltc: float = 0.0,
    interest_rate: float = 0.0,
    loan_fees_pct: float = 0.0,
    solve_residual_land_value: bool = True,
) -> DevelopmentResult:
    """Build the dated project cash flow and returns.

    ``operating_noi`` and the optional income series are indexed by project
    year starting at year 1 (index 0 = year 1) and must cover ``exit_year``.
    ``exit_noi`` is the forward (year exit+1) NOI capitalised at the terminal
    rate. ``opening_year`` is when interest stops being capitalised; it
    defaults to the first year with positive NOI.
    """
    if exit_year < 1:
        raise ValueError("exit_year must be at least 1")
    if terminal_cap_rate <= 0:
        raise ValueError("terminal_cap_rate must be positive")
    if project_hurdle_rate <= -1:
        raise ValueError("project_hurdle_rate is out of range")
    if not 0 <= construction_ltc < 1:
        raise ValueError("construction_ltc must be between 0 and 1")
    if land_cost < 0:
        raise ValueError("land_cost cannot be negative")
    n = exit_year
    noi = _series(operating_noi, n, "operating_noi")
    resi = _series(residential_net_receipts or [], n, "residential_net_receipts", allow_short=True)
    other = _series(other_income or [], n, "other_income", allow_short=True)
    costs = [0.0] * (n + 1)
    for item in cost_items:
        for yr, amt in _spread(item):
            if yr <= n:
                costs[yr] += amt
            else:
                raise ValueError(f"cost item '{item.name}' spends after the exit year")
    if opening_year is None:
        opening_year = next((t for t in range(1, n + 1) if noi[t - 1] > 0), n + 1)
    warnings: list[str] = []

    exit_value = exit_noi / terminal_cap_rate
    exit_net = exit_value * (1.0 - selling_costs_pct)

    def build(land: float) -> tuple[list[DevelopmentYear], list[float], list[float]]:
        rows, unlev, eq = [], [], []
        balance = 0.0
        cum_eq = 0.0
        for t in range(0, n + 1):
            op = noi[t - 1] if t >= 1 else 0.0
            rs = resi[t - 1] if t >= 1 else 0.0
            ot = other[t - 1] if t >= 1 else 0.0
            land_t = land if t == 0 else 0.0
            exit_gross = exit_value if t == n else 0.0
            ucf = -land_t - costs[t] + op + rs + ot + (exit_net if t == n else 0.0)
            # financing
            draw = construction_ltc * costs[t]
            fee = draw * loan_fees_pct
            interest = balance * interest_rate
            if t < opening_year:
                cap, paid = interest, 0.0
            else:
                cap, paid = 0.0, interest
            balance += draw + cap
            repay = balance if t == n else 0.0
            balance -= repay
            ecf = ucf + draw - fee - paid - repay
            cum_eq += ecf
            rows.append(DevelopmentYear(
                year=t, land=land_t, development_costs=costs[t], operating_noi=op, residential_net_receipts=rs,
                other_income=ot, exit_proceeds_gross=exit_gross, unlevered_cash_flow=ucf, loan_draw=draw,
                interest_accrued=interest, interest_capitalised=cap, interest_paid=paid, principal_repaid=repay,
                loan_balance_end=balance, equity_cash_flow=ecf, cumulative_equity=cum_eq,
            ))
            unlev.append(ucf)
            eq.append(ecf)
        return rows, unlev, eq

    rows, unlev, eq = build(land_cost)
    try:
        u_irr = irr(unlev)
    except ValueError as exc:
        raise ValueError(f"unlevered cash flows do not support an IRR: {exc}") from exc
    npv = sum(cf / (1.0 + project_hurdle_rate) ** t for t, cf in enumerate(unlev))
    total_dev = sum(costs)
    fin = sum(r.interest_accrued for r in rows) + sum(r.loan_draw * loan_fees_pct for r in rows)
    total_inv = land_cost + total_dev + fin
    peak_eq = -min(r.cumulative_equity for r in rows)
    peak_debt = max(r.loan_balance_end for r in rows)
    try:
        e_irr = irr(eq)
        contributions = -sum(cf for cf in eq if cf < 0)
        distributions = sum(cf for cf in eq if cf > 0)
        e_mult = distributions / contributions if contributions else None
    except ValueError:
        e_irr, e_mult = None, None
        warnings.append("equity cash flows do not support an IRR")
    payback = next((r.year for r in rows if r.cumulative_equity >= 0 and r.year > 0), None)
    poc = (sum(r.operating_noi + r.residential_net_receipts + r.other_income for r in rows) + exit_net - total_inv) / total_inv if total_inv else 0.0

    rlv = None
    if solve_residual_land_value:
        rlv = _solve_land(build, project_hurdle_rate)
        if rlv is not None and rlv < land_cost:
            warnings.append(f"land cost exceeds the discounted residual of {rlv:,.0f} at a {project_hurdle_rate:.1%} project return")
    if u_irr < project_hurdle_rate:
        warnings.append(f"unlevered IRR {u_irr:.1%} is below the {project_hurdle_rate:.1%} hurdle")
    if any(r.interest_paid > r.operating_noi + r.residential_net_receipts + r.other_income for r in rows if r.year >= opening_year and r.year < n):
        warnings.append("operating income does not cover interest in at least one post-opening year")
    return DevelopmentResult(
        years=rows, total_development_cost=total_dev, total_investment_incl_land_and_finance=total_inv, peak_equity=peak_eq,
        peak_debt=peak_debt, exit_year=n, exit_value=exit_value, exit_net_proceeds=exit_net, unlevered_irr=u_irr,
        unlevered_npv_at_hurdle=npv, project_profit_on_cost=poc, equity_irr=e_irr, equity_multiple=e_mult,
        equity_payback_year=payback, discounted_residual_land_value=rlv, unlevered_cash_flows=unlev, equity_cash_flows=eq,
        warnings=warnings,
    )


def _solve_land(build, hurdle: float) -> float | None:
    """Land payment at year 0 that sets the unlevered IRR to the hurdle (NPV = 0)."""
    _, unlev0, _ = build(0.0)
    npv0 = sum(cf / (1.0 + hurdle) ** t for t, cf in enumerate(unlev0))
    # land enters only at t=0 with factor 1, so NPV(land) = npv0 - land
    return npv0 if npv0 > 0 else max(npv0, 0.0)


def _series(values: Sequence[float], n: int, name: str, allow_short: bool = False) -> list[float]:
    vals = [float(v) for v in values]
    if len(vals) < n:
        if not allow_short and vals:
            raise ValueError(f"{name} must cover {n} years")
        vals = vals + [0.0] * (n - len(vals))
    return vals[:n]


def _spread(item: CostItem) -> list[tuple[int, float]]:
    d = item.duration_years
    if item.profile == "straight" or d == 1:
        w = [1.0 / d] * d
    else:
        raw = [math.sin(math.pi * (i + 0.5) / d) ** 2 for i in range(d)]
        s = sum(raw)
        w = [r / s for r in raw]
    return [(item.start_year + i, item.amount * w[i]) for i in range(d)]
