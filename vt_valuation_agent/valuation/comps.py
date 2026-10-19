"""Relative valuation: trading comparables and precedent transactions."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from typing import Optional

from pydantic import BaseModel, Field

MULTIPLE_FIELDS = ("ev_revenue", "ev_ebitda", "ev_ebit", "pe")
# Which target metric each multiple is applied to, and whether the result is
# enterprise value or equity value.
MULTIPLE_SPEC = {
    "ev_revenue": ("revenue", "enterprise"),
    "ev_ebitda": ("ebitda", "enterprise"),
    "ev_ebit": ("ebit", "enterprise"),
    "pe": ("net_income", "equity"),
}


class Comparable(BaseModel):
    """A peer company or a precedent transaction with its observed multiples."""

    name: str = Field(description="Company or deal name")
    ev_revenue: Optional[float] = Field(default=None, description="EV / Revenue multiple")
    ev_ebitda: Optional[float] = Field(default=None, description="EV / EBITDA multiple")
    ev_ebit: Optional[float] = Field(default=None, description="EV / EBIT multiple")
    pe: Optional[float] = Field(default=None, description="Price / Earnings multiple")
    note: Optional[str] = Field(default=None, description="Optional context, e.g. date or size")


class TargetMetrics(BaseModel):
    """The target's own financial metrics the multiples are applied to."""

    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None
    net_income: Optional[float] = None


@dataclass
class MultipleStats:
    multiple: str
    n: int
    minimum: float
    first_quartile: float
    median: float
    mean: float
    third_quartile: float
    maximum: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ImpliedValuation:
    multiple: str
    target_metric_name: str
    target_metric: float
    basis: str  # "enterprise" or "equity"
    low: dict  # at first quartile
    mid: dict  # at median
    high: dict  # at third quartile

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CompsResult:
    kind: str
    comparables_used: int
    statistics: list[MultipleStats]
    implied: list[ImpliedValuation]
    excluded: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "comparables_used": self.comparables_used,
            "statistics": [s.to_dict() for s in self.statistics],
            "implied": [i.to_dict() for i in self.implied],
            "excluded": self.excluded,
            "notes": self.notes,
        }


def multiple_stats(name: str, values: list[float]) -> MultipleStats:
    clean = sorted(float(v) for v in values if v is not None)
    if not clean:
        raise ValueError(f"no observations for {name}")
    if len(clean) == 1:
        v = clean[0]
        return MultipleStats(name, 1, v, v, v, v, v, v)
    q1, med, q3 = statistics.quantiles(clean, n=4, method="inclusive") if len(clean) >= 2 else (clean[0],) * 3
    return MultipleStats(
        multiple=name,
        n=len(clean),
        minimum=clean[0],
        first_quartile=q1,
        median=med,
        mean=statistics.fmean(clean),
        third_quartile=q3,
        maximum=clean[-1],
    )


def relative_valuation(
    comparables: list[Comparable],
    target: TargetMetrics,
    net_debt: float = 0.0,
    shares_outstanding: float | None = None,
    kind: str = "trading_comps",
    exclude_negative_multiples: bool = True,
) -> CompsResult:
    """Apply peer multiple statistics to the target's metrics.

    For each multiple with at least one observation and a positive target
    metric, implied values are computed at the first quartile (low), median
    (mid) and third quartile (high) of the peer set. Enterprise-value multiples
    are bridged to equity with ``net_debt``; P/E gives equity directly.
    """
    if not comparables:
        raise ValueError("at least one comparable is required")
    stats: list[MultipleStats] = []
    implied: list[ImpliedValuation] = []
    excluded: list[str] = []
    notes: list[str] = []

    for mult in MULTIPLE_FIELDS:
        values = []
        for comp in comparables:
            v = getattr(comp, mult)
            if v is None:
                continue
            if exclude_negative_multiples and v <= 0:
                excluded.append(f"{comp.name}: {mult} = {v} (non-positive, excluded)")
                continue
            values.append(v)
        if not values:
            continue
        st = multiple_stats(mult, values)
        stats.append(st)
        metric_name, basis = MULTIPLE_SPEC[mult]
        metric = getattr(target, metric_name)
        if metric is None:
            notes.append(f"{mult}: target {metric_name} not provided, so no implied value")
            continue
        if metric <= 0:
            notes.append(f"{mult}: target {metric_name} is not positive, multiple not meaningful")
            continue
        implied.append(
            ImpliedValuation(
                multiple=mult,
                target_metric_name=metric_name,
                target_metric=metric,
                basis=basis,
                low=_bridge(st.first_quartile * metric, basis, net_debt, shares_outstanding),
                mid=_bridge(st.median * metric, basis, net_debt, shares_outstanding),
                high=_bridge(st.third_quartile * metric, basis, net_debt, shares_outstanding),
            )
        )
    if not stats:
        raise ValueError("no usable multiples found in the comparables")
    if kind == "precedent_transactions":
        notes.append(
            "precedent multiples embed a control premium and deal-specific synergies; "
            "they typically sit above trading multiples"
        )
    return CompsResult(kind=kind, comparables_used=len(comparables), statistics=stats, implied=implied, excluded=excluded, notes=notes)


def _bridge(value: float, basis: str, net_debt: float, shares: float | None) -> dict:
    if basis == "enterprise":
        ev = value
        equity = value - net_debt
    else:
        equity = value
        ev = value + net_debt
    out = {"enterprise_value": ev, "equity_value": equity}
    if shares:
        out["value_per_share"] = equity / shares
    return out
