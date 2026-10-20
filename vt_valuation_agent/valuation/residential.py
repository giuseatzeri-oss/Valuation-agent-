"""Residential absorption: sales pace, contracted value and cash receipts.

Each unit type sells at its own absorption pace from its launch year. A sale
contracts the unit price (grown at ``price_growth`` to the sale year) and the
buyer pays it in instalments: a reservation share in the sale year, a
construction share spread evenly over the years between the sale and
completion, and the balance at completion (or at sale, if sold after
completion). Selling costs and any brand fee are deducted pro rata from each
receipt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from pydantic import BaseModel, Field


class UnitType(BaseModel):
    name: str
    units: int = Field(gt=0)
    net_saleable_sqm: float = Field(gt=0, description="Net saleable area per unit")
    price_per_sqm: float = Field(gt=0, description="Achieved (not asking) price per sqm in base-year currency")
    launch_year: int = Field(default=1, ge=1, description="First project year in which units are sold")
    absorption_per_year: float = Field(gt=0, description="Units sold per year once launched")
    branded: bool = Field(default=False, description="Whether the brand licence fee applies")


class PaymentSchedule(BaseModel):
    completion_year: int = Field(ge=1, description="Project year in which units are delivered")
    at_reservation: float = Field(default=0.10, ge=0, le=1)
    during_construction: float = Field(default=0.30, ge=0, le=1)
    at_completion: float = Field(default=0.60, ge=0, le=1)


@dataclass
class AbsorptionYear:
    year: int
    units_sold_by_type: dict
    units_sold: int
    contracted_value: float
    gross_receipts: float
    selling_costs: float
    brand_fees: float
    net_receipts: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AbsorptionResult:
    years: list[AbsorptionYear]
    total_units: int
    total_contracted_value: float
    total_net_receipts: float
    sell_out_year_by_type: dict
    average_price_per_sqm: float
    net_receipts_by_year: list[float]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["years"] = [y.to_dict() for y in self.years]
        return d


def residential_absorption(
    unit_types: list[UnitType],
    payment: PaymentSchedule,
    years: int,
    price_growth: float = 0.0,
    selling_costs_pct: float = 0.03,
    brand_fee_pct: float = 0.0,
) -> AbsorptionResult:
    if not unit_types:
        raise ValueError("at least one unit type is required")
    if years <= 0:
        raise ValueError("years must be positive")
    shares = payment.at_reservation + payment.during_construction + payment.at_completion
    if abs(shares - 1.0) > 1e-6:
        raise ValueError(f"payment shares sum to {shares:.3f}, not 1")
    if not 0 <= selling_costs_pct < 1 or not 0 <= brand_fee_pct < 1:
        raise ValueError("cost percentages must be between 0 and 1")
    warnings: list[str] = []

    sold = {ut.name: [0.0] * (years + 1) for ut in unit_types}
    contracted = [0.0] * (years + 1)
    gross = [0.0] * (years + 1)
    fees = [0.0] * (years + 1)
    sell_out: dict[str, int | None] = {}
    total_sqm = 0.0
    total_value = 0.0
    for ut in unit_types:
        remaining = float(ut.units)
        sell_out[ut.name] = None
        for y in range(ut.launch_year, years + 1):
            n = min(ut.absorption_per_year, remaining)
            if n <= 0:
                break
            sold[ut.name][y] = n
            remaining -= n
            price = ut.net_saleable_sqm * ut.price_per_sqm * (1.0 + price_growth) ** (y - 1)
            value = n * price
            contracted[y] += value
            total_value += value
            total_sqm += n * ut.net_saleable_sqm
            fee_rate = brand_fee_pct if ut.branded else 0.0
            for yr, amount in _receipts(value, y, payment, years):
                gross[yr] += amount
                fees[yr] += amount * fee_rate
            if remaining <= 1e-9:
                sell_out[ut.name] = y
        if remaining > 1e-9:
            warnings.append(f"{ut.name}: {remaining:g} units remain unsold at the end of year {years}")
            total_sqm += 0.0
    rows: list[AbsorptionYear] = []
    for y in range(1, years + 1):
        units_by_type = {k: v[y] for k, v in sold.items() if v[y]}
        selling = gross[y] * selling_costs_pct
        rows.append(AbsorptionYear(
            year=y, units_sold_by_type=units_by_type, units_sold=int(round(sum(units_by_type.values()))),
            contracted_value=contracted[y], gross_receipts=gross[y], selling_costs=selling, brand_fees=fees[y],
            net_receipts=gross[y] - selling - fees[y],
        ))
    deferred = sum(gross[years + 1:]) if len(gross) > years + 1 else 0.0
    if deferred:
        warnings.append("some receipts fall after the projection horizon and are excluded")
    return AbsorptionResult(
        years=rows, total_units=sum(ut.units for ut in unit_types), total_contracted_value=total_value,
        total_net_receipts=sum(r.net_receipts for r in rows), sell_out_year_by_type=sell_out,
        average_price_per_sqm=(total_value / total_sqm) if total_sqm else 0.0,
        net_receipts_by_year=[r.net_receipts for r in rows], warnings=warnings,
    )


def _receipts(value: float, sale_year: int, p: PaymentSchedule, years: int) -> list[tuple[int, float]]:
    """Timing of the instalments for a sale in ``sale_year``."""
    out: list[tuple[int, float]] = []
    if sale_year >= p.completion_year:
        return [(min(sale_year, years), value)]
    out.append((sale_year, value * p.at_reservation))
    middle = list(range(sale_year + 1, p.completion_year))
    completion_share = p.at_completion
    if middle:
        per = value * p.during_construction / len(middle)
        out.extend((yr, per) for yr in middle)
    else:
        completion_share += p.during_construction
    out.append((min(p.completion_year, years), value * completion_share))
    return out
