"""Cost of capital: CAPM cost of equity, beta levering and WACC."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class WaccResult:
    cost_of_equity: float
    pre_tax_cost_of_debt: float
    after_tax_cost_of_debt: float
    equity_weight: float
    debt_weight: float
    tax_rate: float
    wacc: float

    def to_dict(self) -> dict:
        return asdict(self)


def cost_of_equity_capm(
    risk_free_rate: float,
    beta: float,
    equity_risk_premium: float,
    size_premium: float = 0.0,
    country_risk_premium: float = 0.0,
    company_specific_premium: float = 0.0,
) -> float:
    """CAPM with optional build-up premia: rf + beta * ERP + premia."""
    return (
        risk_free_rate
        + beta * equity_risk_premium
        + size_premium
        + country_risk_premium
        + company_specific_premium
    )


def after_tax_cost_of_debt(pre_tax_cost_of_debt: float, tax_rate: float) -> float:
    _check_rate("tax_rate", tax_rate)
    return pre_tax_cost_of_debt * (1.0 - tax_rate)


def unlever_beta(levered_beta: float, debt_to_equity: float, tax_rate: float) -> float:
    """Hamada: beta_u = beta_l / (1 + (1 - t) * D/E)."""
    _check_rate("tax_rate", tax_rate)
    if debt_to_equity < 0:
        raise ValueError("debt_to_equity cannot be negative")
    return levered_beta / (1.0 + (1.0 - tax_rate) * debt_to_equity)


def relever_beta(unlevered_beta: float, debt_to_equity: float, tax_rate: float) -> float:
    """Hamada: beta_l = beta_u * (1 + (1 - t) * D/E)."""
    _check_rate("tax_rate", tax_rate)
    if debt_to_equity < 0:
        raise ValueError("debt_to_equity cannot be negative")
    return unlevered_beta * (1.0 + (1.0 - tax_rate) * debt_to_equity)


def wacc(
    cost_of_equity: float,
    pre_tax_cost_of_debt: float,
    tax_rate: float,
    equity_value: float | None = None,
    debt_value: float | None = None,
    debt_weight: float | None = None,
) -> WaccResult:
    """Weighted average cost of capital.

    Provide either market values (``equity_value`` and ``debt_value``) or a
    target ``debt_weight`` (debt / (debt + equity)).
    """
    _check_rate("tax_rate", tax_rate)
    if debt_weight is None:
        if equity_value is None or debt_value is None:
            raise ValueError("provide equity_value and debt_value, or debt_weight")
        if equity_value < 0 or debt_value < 0:
            raise ValueError("equity_value and debt_value cannot be negative")
        total = equity_value + debt_value
        if total == 0:
            raise ValueError("equity_value + debt_value must be positive")
        debt_weight = debt_value / total
    _check_rate("debt_weight", debt_weight)
    equity_weight = 1.0 - debt_weight
    kd_after_tax = after_tax_cost_of_debt(pre_tax_cost_of_debt, tax_rate)
    value = equity_weight * cost_of_equity + debt_weight * kd_after_tax
    return WaccResult(
        cost_of_equity=cost_of_equity,
        pre_tax_cost_of_debt=pre_tax_cost_of_debt,
        after_tax_cost_of_debt=kd_after_tax,
        equity_weight=equity_weight,
        debt_weight=debt_weight,
        tax_rate=tax_rate,
        wacc=value,
    )


def _check_rate(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a decimal between 0 and 1 (got {value})")
