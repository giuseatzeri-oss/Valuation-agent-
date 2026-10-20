"""FIXVAR: fixed and variable component forecast of hotel revenue and expense.

Each revenue and expense line is split into a fixed component, which moves
only with inflation, and a variable component, which moves with inflation and
with a variability index (occupancy, the line's own department revenue, or
total revenue). The index compares the projected year to the base year in
real terms:

    line_t = base x inflation_t x (fixed_pct + variable_pct x index_t / index_base)

The base statement is the subject's expected first stabilised-quality year
stated at the base occupancy and base ADR in current currency. The output is a
USALI-style statement: departmental revenues and expenses, departmental
income, undistributed expenses, gross operating profit, management fees, fixed
charges, the reserve for replacement and net operating income.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal, Optional

from pydantic import BaseModel, Field

DAYS = 365.0

IndexKind = Literal["occupancy", "department_revenue", "total_revenue", "fixed"]


class RevenueLine(BaseModel):
    """A non-rooms revenue department (F&B, spa, beach club, other)."""

    name: str
    base_amount: float = Field(ge=0.0, description="Base-year revenue at base occupancy, current currency")
    fixed_pct: float = Field(default=0.3, ge=0.0, le=1.0, description="Share that does not move with occupancy")


class ExpenseLine(BaseModel):
    """An expense line with its fixed share and variability index."""

    name: str
    base_amount: float = Field(ge=0.0, description="Base-year amount at base utilisation, current currency")
    fixed_pct: float = Field(ge=0.0, le=1.0)
    index: IndexKind = Field(default="total_revenue", description="What the variable component follows")
    department: Optional[str] = Field(default=None, description="For departmental expenses: 'rooms' or the revenue line name")


@dataclass
class StatementYear:
    year: int
    occupancy: float
    adr: float
    occupied_rooms: float
    inflation_factor: float
    revenues: dict
    total_revenue: float
    departmental_expenses: dict
    departmental_income: float
    undistributed_expenses: dict
    gross_operating_profit: float
    gop_margin: float
    management_fees: float
    income_before_fixed_charges: float
    fixed_charges: dict
    reserve_for_replacement: float
    net_operating_income: float
    noi_margin: float
    noi_per_available_room: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProFormaResult:
    rooms: int
    years: list[StatementYear]
    noi_by_year: list[float]
    total_revenue_by_year: list[float]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "rooms": self.rooms,
            "years": [y.to_dict() for y in self.years],
            "noi_by_year": self.noi_by_year,
            "total_revenue_by_year": self.total_revenue_by_year,
            "warnings": self.warnings,
        }


def fixvar_proforma(
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
) -> ProFormaResult:
    """Project the operating statement year by year.

    ``adr`` is nominal (already inflated, as the RNAADR output gives it);
    ``base_adr`` is in base-year currency. Rooms department expenses should
    use ``index='occupancy'``; other departmental expenses usually follow
    ``department_revenue``; undistributed expenses and variable fixed charges
    follow ``total_revenue``; property tax and insurance are normally
    ``fixed``.
    """
    if rooms <= 0:
        raise ValueError("rooms must be positive")
    n = len(occupancy)
    if n == 0 or len(adr) != n:
        raise ValueError("occupancy and adr must have the same positive length")
    if not 0 < base_occupancy <= 1:
        raise ValueError("base_occupancy must be between 0 and 1")
    if base_adr <= 0:
        raise ValueError("base_adr must be positive")
    if available_rooms_fraction is not None and len(available_rooms_fraction) != n:
        raise ValueError("available_rooms_fraction needs one entry per year")
    rev_names = {"rooms"} | {r.name for r in other_revenues}
    for e in departmental_expenses:
        if e.department not in rev_names:
            raise ValueError(f"departmental expense '{e.name}' names unknown department '{e.department}'")
    warnings: list[str] = []

    base_rooms_rev = rooms * DAYS * base_occupancy * base_adr
    base_total_rev = base_rooms_rev + sum(r.base_amount for r in other_revenues)
    years: list[StatementYear] = []
    for t in range(1, n + 1):
        infl = (1.0 + inflation) ** t
        avail = rooms * DAYS * (available_rooms_fraction[t - 1] if available_rooms_fraction else 1.0)
        occ = occupancy[t - 1]
        occupied = avail * occ
        occ_index = occ / base_occupancy
        revenues = {"rooms": occupied * adr[t - 1]}
        for r in other_revenues:
            revenues[r.name] = r.base_amount * infl * (r.fixed_pct + (1 - r.fixed_pct) * occ_index)
        total_rev = sum(revenues.values())
        total_index = (total_rev / infl) / base_total_rev if base_total_rev else 1.0

        def project(line: ExpenseLine) -> float:
            if line.index == "fixed":
                idx = 1.0
            elif line.index == "occupancy":
                idx = occ_index
            elif line.index == "total_revenue":
                idx = total_index
            else:  # department_revenue
                dept = line.department or "rooms"
                base_dept = base_rooms_rev if dept == "rooms" else next(r.base_amount for r in other_revenues if r.name == dept)
                idx = (revenues[dept] / infl) / base_dept if base_dept else 1.0
            return line.base_amount * infl * (line.fixed_pct + (1 - line.fixed_pct) * idx)

        dept_exp = {e.name: project(e) for e in departmental_expenses}
        dept_income = total_rev - sum(dept_exp.values())
        undist = {e.name: project(e) for e in undistributed_expenses}
        gop = dept_income - sum(undist.values())
        mgmt = base_management_fee_pct * total_rev + incentive_fee_pct_of_gop * max(gop, 0.0)
        ibfc = gop - mgmt
        fixed = {e.name: project(e) for e in fixed_charges}
        reserve = reserve_pct * total_rev
        noi = ibfc - sum(fixed.values()) - reserve
        years.append(StatementYear(
            year=t, occupancy=occ, adr=adr[t - 1], occupied_rooms=occupied, inflation_factor=infl,
            revenues=revenues, total_revenue=total_rev, departmental_expenses=dept_exp, departmental_income=dept_income,
            undistributed_expenses=undist, gross_operating_profit=gop, gop_margin=(gop / total_rev) if total_rev else 0.0,
            management_fees=mgmt, income_before_fixed_charges=ibfc, fixed_charges=fixed, reserve_for_replacement=reserve,
            net_operating_income=noi, noi_margin=(noi / total_rev) if total_rev else 0.0,
            noi_per_available_room=noi / rooms,
        ))
    last = years[-1]
    if last.gop_margin > 0.50:
        warnings.append(f"stabilised GOP margin {last.gop_margin:.0%} is above 50%; check the expense base statement")
    if last.gop_margin < 0.20:
        warnings.append(f"stabilised GOP margin {last.gop_margin:.0%} is below 20%; the cost base may be heavy for the revenue")
    if any(y.net_operating_income < 0 for y in years):
        warnings.append("net operating income is negative in at least one year; working capital must cover the shortfall")
    return ProFormaResult(rooms=rooms, years=years, noi_by_year=[y.net_operating_income for y in years],
                          total_revenue_by_year=[y.total_revenue for y in years], warnings=warnings)
