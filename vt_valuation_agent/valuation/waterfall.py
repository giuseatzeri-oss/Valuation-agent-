"""Equity waterfall with IRR hurdles, optional catch-up and promote.

Contributed capital is pari passu between the LP and the GP co-invest in the
``lp_capital_share`` proportion. Each tier returns a ``capital_share`` of
distributions to capital and the remainder to the GP as promote, until the
capital holders have achieved the tier's hurdle IRR (tracked with a balance
account that accrues at the hurdle rate). An optional catch-up pays the GP a
``catch_up_pct`` share of distributions after the first hurdle until the
promote equals ``catch_up_to_promote`` of all profits distributed so far.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional, Sequence

from pydantic import BaseModel, Field

from .finance_math import irr


class WaterfallTier(BaseModel):
    hurdle_irr: Optional[float] = Field(default=None, description="Capital IRR up to which this tier applies; None for the final tier")
    capital_share: float = Field(ge=0, le=1, description="Share of this tier's distributions paid to capital pari passu; the rest is promote")


@dataclass
class WaterfallPeriod:
    period: int
    contribution: float
    lp_contribution: float
    gp_contribution: float
    distribution: float
    to_capital: float
    lp_distribution: float
    gp_coinvest_distribution: float
    promote: float
    by_tier: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WaterfallResult:
    periods: list[WaterfallPeriod]
    total_contributions: float
    total_distributions: float
    total_to_capital: float
    total_promote: float
    promote_share_of_profit: float
    lp_irr: float | None
    lp_multiple: float
    gp_irr: float | None
    gp_multiple: float | None
    capital_irr_before_promote: float | None
    lp_cash_flows: list[float]
    gp_cash_flows: list[float]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["periods"] = [p.to_dict() for p in self.periods]
        return d


def equity_waterfall(
    cash_flows: Sequence[float],
    tiers: list[WaterfallTier],
    lp_capital_share: float = 1.0,
    catch_up_pct: Optional[float] = None,
    catch_up_to_promote: Optional[float] = None,
) -> WaterfallResult:
    """Distribute total equity cash flows (period 0..n, negatives are
    contributions) through the tiers."""
    flows = [float(x) for x in cash_flows]
    if len(flows) < 2:
        raise ValueError("cash_flows needs at least two periods")
    if not tiers:
        raise ValueError("at least one tier is required")
    if tiers[-1].hurdle_irr is not None:
        raise ValueError("the final tier must have hurdle_irr = None")
    for a, b in zip(tiers, tiers[1:]):
        if b.hurdle_irr is not None and a.hurdle_irr is not None and b.hurdle_irr <= a.hurdle_irr:
            raise ValueError("tier hurdles must increase")
    if not 0 < lp_capital_share <= 1:
        raise ValueError("lp_capital_share must be between 0 and 1")
    if (catch_up_pct is None) != (catch_up_to_promote is None):
        raise ValueError("catch_up_pct and catch_up_to_promote go together")
    if catch_up_to_promote is not None and not 0 <= catch_up_to_promote < 1:
        raise ValueError("catch_up_to_promote must be between 0 and 1")
    warnings: list[str] = []

    hurdles = [t.hurdle_irr for t in tiers if t.hurdle_irr is not None]
    balances = [0.0] * len(hurdles)  # capital's unreturned balance at each hurdle rate
    cum_contrib = cum_capital_dist = cum_promote = 0.0
    periods: list[WaterfallPeriod] = []
    lp_cfs: list[float] = []
    gp_cfs: list[float] = []
    for t, cf in enumerate(flows):
        if t > 0:
            balances = [b * (1.0 + r) for b, r in zip(balances, hurdles)]
        contribution = -cf if cf < 0 else 0.0
        distribution = cf if cf > 0 else 0.0
        if contribution:
            balances = [b + contribution for b in balances]
            cum_contrib += contribution
        remaining = distribution
        to_capital = promote = 0.0
        by_tier: dict[str, float] = {}
        for k, tier in enumerate(tiers):
            if remaining <= 1e-12:
                break
            if tier.hurdle_irr is not None:
                need = max(balances[k], 0.0)
                if need <= 1e-12:
                    amount = 0.0
                else:
                    amount = min(remaining, need / tier.capital_share) if tier.capital_share > 0 else remaining
            else:
                amount = remaining
            cap_part = amount * tier.capital_share
            pro_part = amount - cap_part
            to_capital += cap_part
            promote += pro_part
            remaining -= amount
            balances = [b - cap_part for b in balances]
            by_tier[f"tier_{k + 1}"] = amount
            # catch-up after the first hurdle tier
            if k == 0 and catch_up_pct is not None and remaining > 1e-12:
                profit_capital = cum_capital_dist + to_capital - cum_contrib
                target = catch_up_to_promote / (1.0 - catch_up_to_promote) * max(profit_capital, 0.0)
                gap = max(target - (cum_promote + promote), 0.0)
                if gap > 0 and catch_up_pct > 0:
                    amount = min(remaining, gap / catch_up_pct)
                    pro_part = amount * catch_up_pct
                    cap_part = amount - pro_part
                    promote += pro_part
                    to_capital += cap_part
                    remaining -= amount
                    balances = [b - cap_part for b in balances]
                    by_tier["catch_up"] = amount
        cum_capital_dist += to_capital
        cum_promote += promote
        lp_c = contribution * lp_capital_share
        gp_c = contribution - lp_c
        lp_d = to_capital * lp_capital_share
        gp_d = to_capital - lp_d
        periods.append(WaterfallPeriod(
            period=t, contribution=contribution, lp_contribution=lp_c, gp_contribution=gp_c, distribution=distribution,
            to_capital=to_capital, lp_distribution=lp_d, gp_coinvest_distribution=gp_d, promote=promote, by_tier=by_tier,
        ))
        lp_cfs.append(lp_d - lp_c)
        gp_cfs.append(gp_d + promote - gp_c)
    total_dist = sum(p.distribution for p in periods)
    profit = total_dist - cum_contrib
    lp_contrib = sum(p.lp_contribution for p in periods)
    gp_contrib = sum(p.gp_contribution for p in periods)
    lp_mult = sum(p.lp_distribution for p in periods) / lp_contrib if lp_contrib else 0.0
    gp_mult = (sum(p.gp_coinvest_distribution + p.promote for p in periods) / gp_contrib) if gp_contrib else None
    if profit <= 0:
        warnings.append("the deal returns less than the capital contributed; no promote is earned")
    return WaterfallResult(
        periods=periods, total_contributions=cum_contrib, total_distributions=total_dist, total_to_capital=cum_capital_dist,
        total_promote=cum_promote, promote_share_of_profit=(cum_promote / profit) if profit > 0 else 0.0,
        lp_irr=_safe_irr(lp_cfs), lp_multiple=lp_mult, gp_irr=_safe_irr(gp_cfs), gp_multiple=gp_mult,
        capital_irr_before_promote=_safe_irr(flows), lp_cash_flows=lp_cfs, gp_cash_flows=gp_cfs, warnings=warnings,
    )


def _safe_irr(flows: Sequence[float]) -> float | None:
    try:
        return irr(flows)
    except ValueError:
        return None
