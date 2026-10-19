"""Core time-value-of-money helpers shared by the valuation modules.

Conventions used across the engine:
- Rates are decimals (0.085 means 8.5%).
- Cash flows are in a single consistent currency unit (e.g. USD millions).
- Period 1 is one full period after the valuation date unless a
  ``mid_year`` convention is requested, in which case cash flow ``t`` is
  discounted at ``t - 0.5``.
"""

from __future__ import annotations

from typing import Sequence


def discount_factor(rate: float, period: float) -> float:
    """Return 1 / (1 + rate) ** period."""
    if rate <= -1.0:
        raise ValueError("rate must be greater than -100%")
    return 1.0 / (1.0 + rate) ** period


def npv(rate: float, cash_flows: Sequence[float], mid_year: bool = False) -> float:
    """Net present value of cash flows occurring in periods 1..n.

    With ``mid_year=True`` each flow is assumed to arrive halfway through its
    period, so flow ``t`` is discounted over ``t - 0.5`` periods.
    """
    offset = 0.5 if mid_year else 0.0
    return sum(cf * discount_factor(rate, t - offset) for t, cf in enumerate(cash_flows, start=1))


def irr(cash_flows: Sequence[float], lower: float = -0.99, upper: float = 10.0, tol: float = 1e-10, max_iter: int = 500) -> float:
    """Internal rate of return of cash flows in periods 0..n via bisection.

    The first flow is at time 0 (typically a negative investment). Raises
    ``ValueError`` when the flows do not change sign, since no IRR exists.
    """
    flows = list(cash_flows)
    if len(flows) < 2:
        raise ValueError("irr needs at least two cash flows")
    if all(cf >= 0 for cf in flows) or all(cf <= 0 for cf in flows):
        raise ValueError("cash flows must contain both inflows and outflows for an IRR to exist")

    def f(rate: float) -> float:
        return sum(cf / (1.0 + rate) ** t for t, cf in enumerate(flows))

    lo, hi = lower, upper
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0:
        raise ValueError("could not bracket an IRR between %.0f%% and %.0f%%" % (lower * 100, upper * 100))
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        f_mid = f(mid)
        if abs(f_mid) < tol or (hi - lo) / 2.0 < tol:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2.0


def cagr(begin: float, end: float, years: float) -> float:
    """Compound annual growth rate between two positive values."""
    if begin <= 0 or end <= 0:
        raise ValueError("cagr requires positive begin and end values")
    if years <= 0:
        raise ValueError("years must be positive")
    return (end / begin) ** (1.0 / years) - 1.0


def safe_divide(numerator: float, denominator: float) -> float | None:
    """Return numerator / denominator, or None when the denominator is zero."""
    if denominator == 0:
        return None
    return numerator / denominator
