"""Unlevered discounted cash flow valuation.

Two terminal value methods are supported:

- Perpetuity (Gordon) growth: ``TV = FCF_n * (1 + g) / (r - g)``. With the
  mid-year convention the terminal value is discounted over ``n - 0.5``
  periods, consistent with the final-year cash flow timing.
- Exit multiple: ``TV = multiple * terminal_metric`` (e.g. year-n EBITDA),
  always discounted over ``n`` full periods because the multiple is applied to
  a year-end metric.

The enterprise-to-equity bridge subtracts net debt, minority interest and
preferred stock, and adds non-operating assets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Sequence

from .finance_math import discount_factor


@dataclass
class ProjectionYear:
    year: int
    revenue: float
    ebitda: float
    depreciation_amortization: float
    ebit: float
    taxes: float
    nopat: float
    capex: float
    change_in_nwc: float
    unlevered_fcf: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DcfResult:
    discount_rate: float
    terminal_method: str
    mid_year: bool
    cash_flows: list[float]
    discount_factors: list[float]
    pv_cash_flows: list[float]
    sum_pv_cash_flows: float
    terminal_value: float
    pv_terminal_value: float
    terminal_value_pct_of_ev: float
    enterprise_value: float
    net_debt: float
    minority_interest: float
    preferred_stock: float
    non_operating_assets: float
    equity_value: float
    shares_outstanding: float | None
    value_per_share: float | None
    terminal_growth: float | None = None
    exit_multiple: float | None = None
    terminal_metric: float | None = None
    implied_exit_multiple: float | None = None
    implied_terminal_growth: float | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def project_free_cash_flows(
    base_revenue: float,
    revenue_growth: Sequence[float],
    ebitda_margin: float | Sequence[float],
    da_pct_revenue: float,
    capex_pct_revenue: float,
    nwc_pct_revenue: float,
    tax_rate: float,
    base_nwc: float | None = None,
) -> list[ProjectionYear]:
    """Build an explicit-period unlevered free cash flow schedule.

    ``revenue_growth`` has one entry per projection year. ``ebitda_margin`` is
    a single margin or one margin per year. Net working capital is modelled as
    ``nwc_pct_revenue`` of revenue; the cash flow impact is the year-on-year
    change (``base_nwc`` defaults to ``nwc_pct_revenue * base_revenue``).
    Taxes are charged on EBIT (unlevered), floored at zero.
    """
    years = len(revenue_growth)
    if years == 0:
        raise ValueError("revenue_growth must contain at least one year")
    margins = _expand(ebitda_margin, years, "ebitda_margin")
    if not 0.0 <= tax_rate <= 1.0:
        raise ValueError("tax_rate must be a decimal between 0 and 1")

    schedule: list[ProjectionYear] = []
    revenue = base_revenue
    prev_nwc = base_nwc if base_nwc is not None else nwc_pct_revenue * base_revenue
    for i in range(years):
        revenue = revenue * (1.0 + revenue_growth[i])
        ebitda = revenue * margins[i]
        da = revenue * da_pct_revenue
        ebit = ebitda - da
        taxes = max(ebit, 0.0) * tax_rate
        nopat = ebit - taxes
        capex = revenue * capex_pct_revenue
        nwc = revenue * nwc_pct_revenue
        delta_nwc = nwc - prev_nwc
        prev_nwc = nwc
        fcf = nopat + da - capex - delta_nwc
        schedule.append(
            ProjectionYear(
                year=i + 1,
                revenue=revenue,
                ebitda=ebitda,
                depreciation_amortization=da,
                ebit=ebit,
                taxes=taxes,
                nopat=nopat,
                capex=capex,
                change_in_nwc=delta_nwc,
                unlevered_fcf=fcf,
            )
        )
    return schedule


def dcf_valuation(
    free_cash_flows: Sequence[float],
    discount_rate: float,
    terminal_growth: float | None = None,
    exit_multiple: float | None = None,
    terminal_metric: float | None = None,
    mid_year: bool = False,
    net_debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_stock: float = 0.0,
    non_operating_assets: float = 0.0,
    shares_outstanding: float | None = None,
) -> DcfResult:
    """Value a business from explicit unlevered free cash flows.

    Exactly one of ``terminal_growth`` or ``exit_multiple`` must be given.
    When ``exit_multiple`` is used, ``terminal_metric`` (the year-n metric the
    multiple applies to, e.g. EBITDA) is required.
    """
    flows = [float(cf) for cf in free_cash_flows]
    if not flows:
        raise ValueError("free_cash_flows must contain at least one year")
    if discount_rate <= 0:
        raise ValueError("discount_rate must be positive")
    if (terminal_growth is None) == (exit_multiple is None):
        raise ValueError("provide exactly one of terminal_growth or exit_multiple")

    n = len(flows)
    offset = 0.5 if mid_year else 0.0
    factors = [discount_factor(discount_rate, t - offset) for t in range(1, n + 1)]
    pvs = [cf * df for cf, df in zip(flows, factors)]
    sum_pv = sum(pvs)
    warnings: list[str] = []

    implied_multiple = None
    implied_growth = None
    if terminal_growth is not None:
        if terminal_growth >= discount_rate:
            raise ValueError("terminal_growth must be below discount_rate for a perpetuity to converge")
        method = "perpetuity_growth"
        terminal_value = flows[-1] * (1.0 + terminal_growth) / (discount_rate - terminal_growth)
        tv_factor = discount_factor(discount_rate, n - offset)
        if terminal_metric:
            implied_multiple = terminal_value / terminal_metric
        if terminal_growth > 0.04:
            warnings.append("terminal growth above 4% exceeds long-run nominal GDP growth for most economies")
    else:
        assert exit_multiple is not None
        if terminal_metric is None:
            raise ValueError("terminal_metric is required with exit_multiple")
        if exit_multiple <= 0:
            raise ValueError("exit_multiple must be positive")
        method = "exit_multiple"
        terminal_value = exit_multiple * terminal_metric
        tv_factor = discount_factor(discount_rate, n)
        if terminal_value + flows[-1] != 0:
            implied_growth = (terminal_value * discount_rate - flows[-1]) / (terminal_value + flows[-1])
            if implied_growth > 0.05:
                warnings.append(
                    "exit multiple implies a perpetual growth rate above 5%; the multiple may be aggressive"
                )

    pv_tv = terminal_value * tv_factor
    ev = sum_pv + pv_tv
    tv_share = pv_tv / ev if ev else 0.0
    if tv_share > 0.75:
        warnings.append("terminal value is more than 75% of enterprise value; the valuation is highly sensitive to terminal assumptions")
    if flows[-1] <= 0:
        warnings.append("final-year free cash flow is not positive, so the terminal value is unreliable")

    equity = ev - net_debt - minority_interest - preferred_stock + non_operating_assets
    per_share = None
    if shares_outstanding is not None:
        if shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be positive")
        per_share = equity / shares_outstanding

    return DcfResult(
        discount_rate=discount_rate,
        terminal_method=method,
        mid_year=mid_year,
        cash_flows=flows,
        discount_factors=factors,
        pv_cash_flows=pvs,
        sum_pv_cash_flows=sum_pv,
        terminal_value=terminal_value,
        pv_terminal_value=pv_tv,
        terminal_value_pct_of_ev=tv_share,
        enterprise_value=ev,
        net_debt=net_debt,
        minority_interest=minority_interest,
        preferred_stock=preferred_stock,
        non_operating_assets=non_operating_assets,
        equity_value=equity,
        shares_outstanding=shares_outstanding,
        value_per_share=per_share,
        terminal_growth=terminal_growth,
        exit_multiple=exit_multiple,
        terminal_metric=terminal_metric,
        implied_exit_multiple=implied_multiple,
        implied_terminal_growth=implied_growth,
        warnings=warnings,
    )


def _expand(value: float | Sequence[float], years: int, name: str) -> list[float]:
    if isinstance(value, (int, float)):
        return [float(value)] * years
    values = [float(v) for v in value]
    if len(values) != years:
        raise ValueError(f"{name} must have one entry per projection year ({years}), got {len(values)}")
    return values
