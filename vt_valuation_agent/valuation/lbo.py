"""A compact annual leveraged buyout returns model.

The model is deliberately simple and transparent: a single tranche of debt at
a blended interest rate, cash taxes on EBIT, maintenance capex and working
capital as percentages of EBITDA, and a cash sweep that applies free cash
flow to debt paydown. It is meant for quick returns triangulation, not for
replacing a full operating model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Sequence

from .finance_math import irr


@dataclass
class LboYear:
    year: int
    ebitda: float
    depreciation_amortization: float
    ebit: float
    interest: float
    taxes: float
    capex: float
    change_in_nwc: float
    free_cash_flow: float
    debt_repaid: float
    ending_debt: float
    ending_cash: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LboResult:
    entry_enterprise_value: float
    entry_debt: float
    entry_equity: float
    transaction_fees: float
    exit_enterprise_value: float
    exit_net_debt: float
    exit_equity: float
    moic: float
    irr: float
    hold_years: int
    schedule: list[LboYear]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["schedule"] = [y.to_dict() for y in self.schedule]
        return d


def lbo_returns(
    entry_ebitda: float,
    entry_multiple: float,
    exit_multiple: float,
    ebitda_growth: Sequence[float],
    leverage_multiple: float,
    interest_rate: float,
    tax_rate: float,
    da_pct_ebitda: float = 0.0,
    capex_pct_ebitda: float = 0.0,
    nwc_pct_ebitda_change: float = 0.0,
    cash_sweep: float = 1.0,
    fees_pct_ev: float = 0.02,
) -> LboResult:
    """Compute sponsor MOIC and IRR for a simple LBO.

    ``ebitda_growth`` holds one growth rate per hold year. ``leverage_multiple``
    is entry debt / entry EBITDA. ``nwc_pct_ebitda_change`` is the working
    capital investment per unit of EBITDA growth. Transaction fees are funded
    by the sponsor's equity cheque.
    """
    if entry_ebitda <= 0:
        raise ValueError("entry_ebitda must be positive")
    if entry_multiple <= 0 or exit_multiple <= 0:
        raise ValueError("entry and exit multiples must be positive")
    if not ebitda_growth:
        raise ValueError("ebitda_growth must contain at least one hold year")
    if leverage_multiple < 0:
        raise ValueError("leverage_multiple cannot be negative")
    if not 0.0 <= cash_sweep <= 1.0:
        raise ValueError("cash_sweep must be between 0 and 1")
    if not 0.0 <= tax_rate <= 1.0:
        raise ValueError("tax_rate must be a decimal between 0 and 1")

    warnings: list[str] = []
    entry_ev = entry_ebitda * entry_multiple
    debt = entry_ebitda * leverage_multiple
    fees = entry_ev * fees_pct_ev
    equity_in = entry_ev - debt + fees
    if equity_in <= 0:
        raise ValueError("leverage exceeds the entry enterprise value; equity cheque would be non-positive")
    if leverage_multiple > 6.5:
        warnings.append("leverage above 6.5x EBITDA is aggressive relative to typical sponsor financing")

    schedule: list[LboYear] = []
    ebitda = entry_ebitda
    cash = 0.0
    for i, g in enumerate(ebitda_growth, start=1):
        prev_ebitda = ebitda
        ebitda = ebitda * (1.0 + g)
        da = ebitda * da_pct_ebitda
        ebit = ebitda - da
        interest = debt * interest_rate
        taxes = max(ebit - interest, 0.0) * tax_rate
        capex = ebitda * capex_pct_ebitda
        delta_nwc = (ebitda - prev_ebitda) * nwc_pct_ebitda_change
        fcf = ebitda - interest - taxes - capex - delta_nwc
        repay = min(max(fcf, 0.0) * cash_sweep, debt)
        debt -= repay
        cash += fcf - repay
        schedule.append(
            LboYear(
                year=i,
                ebitda=ebitda,
                depreciation_amortization=da,
                ebit=ebit,
                interest=interest,
                taxes=taxes,
                capex=capex,
                change_in_nwc=delta_nwc,
                free_cash_flow=fcf,
                debt_repaid=repay,
                ending_debt=debt,
                ending_cash=cash,
            )
        )
        if fcf < 0:
            warnings.append(f"year {i}: negative free cash flow after interest; the structure may need more equity")

    exit_ev = ebitda * exit_multiple
    exit_net_debt = debt - cash
    exit_equity = exit_ev - exit_net_debt
    if exit_equity <= 0:
        raise ValueError("exit equity is not positive; the deal does not return capital")
    moic = exit_equity / equity_in
    hold = len(schedule)
    rate = irr([-equity_in] + [0.0] * (hold - 1) + [exit_equity])
    if exit_multiple > entry_multiple:
        warnings.append("exit multiple above entry multiple assumes multiple expansion; test returns at a flat multiple")

    return LboResult(
        entry_enterprise_value=entry_ev,
        entry_debt=entry_ebitda * leverage_multiple,
        entry_equity=equity_in,
        transaction_fees=fees,
        exit_enterprise_value=exit_ev,
        exit_net_debt=exit_net_debt,
        exit_equity=exit_equity,
        moic=moic,
        irr=rate,
        hold_years=hold,
        schedule=schedule,
        warnings=warnings,
    )


def max_entry_multiple_for_irr(target_irr: float, lo: float = 1.0, hi: float = 40.0, tol: float = 1e-4, **kwargs) -> float:
    """Highest entry multiple that still achieves ``target_irr`` (bisection).

    ``kwargs`` are passed to :func:`lbo_returns` and must include every
    required argument except ``entry_multiple``.
    """
    def irr_at(multiple: float) -> float:
        try:
            return lbo_returns(entry_multiple=multiple, **kwargs).irr
        except ValueError:
            return -1.0

    # The equity cheque is positive only when multiple * (1 + fees) > leverage,
    # so start the bracket just above that floor.
    leverage = float(kwargs.get("leverage_multiple", 0.0))
    fees = float(kwargs.get("fees_pct_ev", 0.02))
    lo = max(lo, leverage / (1.0 + fees) + 1e-3)
    if hi <= lo:
        raise ValueError("upper bound must exceed the minimum feasible entry multiple")
    if irr_at(lo) < target_irr:
        raise ValueError("target IRR is not achievable even at the lowest feasible entry multiple")
    if irr_at(hi) >= target_irr:
        return hi
    while hi - lo > tol:
        mid = (lo + hi) / 2.0
        if irr_at(mid) >= target_irr:
            lo = mid
        else:
            hi = mid
    return lo
