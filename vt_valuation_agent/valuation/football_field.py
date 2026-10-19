"""Assemble valuation ranges from several methods into a football field."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from typing import Optional

from pydantic import BaseModel, Field


class ValuationRange(BaseModel):
    """One bar on the football field."""

    method: str = Field(description="e.g. 'DCF (perpetuity)', 'Trading comps EV/EBITDA', '52-week range'")
    low: float = Field(description="Low end of the range")
    high: float = Field(description="High end of the range")
    mid: Optional[float] = Field(default=None, description="Point estimate; defaults to the midpoint")
    basis: str = Field(default="enterprise", description="'enterprise' or 'equity' or 'per_share'")
    weight: float = Field(default=1.0, ge=0.0, description="Relative weight in the blended value")


@dataclass
class FootballFieldBar:
    method: str
    weight: float
    enterprise_low: float | None
    enterprise_mid: float | None
    enterprise_high: float | None
    equity_low: float | None
    equity_mid: float | None
    equity_high: float | None
    per_share_low: float | None
    per_share_mid: float | None
    per_share_high: float | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FootballField:
    bars: list[FootballFieldBar]
    overall_low: dict
    overall_high: dict
    weighted_mid: dict
    median_mid: dict
    net_debt: float
    shares_outstanding: float | None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["bars"] = [b.to_dict() for b in self.bars]
        return d


def football_field(
    ranges: list[ValuationRange],
    net_debt: float = 0.0,
    shares_outstanding: float | None = None,
) -> FootballField:
    """Normalise every range to enterprise, equity and per-share terms.

    Ranges supplied on a per-share basis require ``shares_outstanding``.
    The blended value is the weight-averaged midpoint; the median of
    midpoints is also reported as a robustness check.
    """
    if not ranges:
        raise ValueError("at least one valuation range is required")
    bars: list[FootballFieldBar] = []
    notes: list[str] = []
    for r in ranges:
        if r.high < r.low:
            raise ValueError(f"{r.method}: high must be >= low")
        mid = r.mid if r.mid is not None else (r.low + r.high) / 2.0
        trip = {}
        for label, v in (("low", r.low), ("mid", mid), ("high", r.high)):
            trip[label] = _normalise(v, r.basis, net_debt, shares_outstanding)
        bars.append(
            FootballFieldBar(
                method=r.method,
                weight=r.weight,
                enterprise_low=trip["low"]["enterprise"],
                enterprise_mid=trip["mid"]["enterprise"],
                enterprise_high=trip["high"]["enterprise"],
                equity_low=trip["low"]["equity"],
                equity_mid=trip["mid"]["equity"],
                equity_high=trip["high"]["equity"],
                per_share_low=trip["low"]["per_share"],
                per_share_mid=trip["mid"]["per_share"],
                per_share_high=trip["high"]["per_share"],
            )
        )

    total_w = sum(b.weight for b in bars)
    if total_w <= 0:
        raise ValueError("weights must sum to a positive number")

    def agg(attr_low: str, attr_mid: str, attr_high: str) -> tuple:
        lows = [getattr(b, attr_low) for b in bars if getattr(b, attr_low) is not None]
        highs = [getattr(b, attr_high) for b in bars if getattr(b, attr_high) is not None]
        mids = [(getattr(b, attr_mid), b.weight) for b in bars if getattr(b, attr_mid) is not None]
        if not mids:
            return None, None, None, None
        w_mid = sum(m * w for m, w in mids) / sum(w for _, w in mids)
        return min(lows), max(highs), w_mid, statistics.median(m for m, _ in mids)

    ev = agg("enterprise_low", "enterprise_mid", "enterprise_high")
    eq = agg("equity_low", "equity_mid", "equity_high")
    ps = agg("per_share_low", "per_share_mid", "per_share_high")
    if shares_outstanding is None:
        notes.append("shares_outstanding not provided, so per-share values are omitted")
    spread = (ev[1] - ev[0]) / ev[2] if ev[2] else None
    if spread is not None and spread > 1.0:
        notes.append("the overall range spans more than 100% of the blended value; the methods disagree materially")
    return FootballField(
        bars=bars,
        overall_low={"enterprise": ev[0], "equity": eq[0], "per_share": ps[0]},
        overall_high={"enterprise": ev[1], "equity": eq[1], "per_share": ps[1]},
        weighted_mid={"enterprise": ev[2], "equity": eq[2], "per_share": ps[2]},
        median_mid={"enterprise": ev[3], "equity": eq[3], "per_share": ps[3]},
        net_debt=net_debt,
        shares_outstanding=shares_outstanding,
        notes=notes,
    )


def _normalise(value: float, basis: str, net_debt: float, shares: float | None) -> dict:
    if basis == "enterprise":
        ev, equity = value, value - net_debt
    elif basis == "equity":
        ev, equity = value + net_debt, value
    elif basis == "per_share":
        if not shares:
            raise ValueError("per_share ranges require shares_outstanding")
        equity = value * shares
        ev = equity + net_debt
    else:
        raise ValueError(f"unknown basis '{basis}' (use enterprise, equity or per_share)")
    return {"enterprise": ev, "equity": equity, "per_share": (equity / shares) if shares else None}
