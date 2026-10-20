"""Residual land value for a greenfield hotel or resort.

    RLV = stabilised property value (deferred to today)
          - hard costs - site works - soft costs - FF&E and OS&E
          - pre-opening and working capital - contingency
          - construction financing costs - developer profit

The stabilised value is normally the mortgage-equity value at stabilisation.
Because it is realised only after the development and ramp-up period it is
deferred to the valuation date at the discount rate. Construction interest is
approximated on the average drawn balance over the construction period.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class ResidualLandValueResult:
    stabilised_value: float
    deferral_years: float
    discount_rate: float
    present_value_of_stabilised_asset: float
    hard_costs: float
    site_works: float
    soft_costs: float
    ffe_ose: float
    preopening_working_capital: float
    contingency: float
    development_cost_ex_land_ex_finance: float
    financing_costs: float
    developer_profit: float
    residual_land_value: float
    land_transaction_costs_pct: float
    max_land_bid_net_of_costs: float
    asking_land_price: float | None
    headroom_vs_asking: float | None
    profit_on_cost_at_asking: float | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def residual_land_value(
    stabilised_value: float,
    hard_costs: float,
    soft_costs: float,
    ffe_ose: float = 0.0,
    site_works: float = 0.0,
    preopening_working_capital: float = 0.0,
    contingency_pct_of_hard: float = 0.075,
    deferral_years: float = 0.0,
    discount_rate: float = 0.0,
    construction_ltc: float = 0.0,
    construction_interest_rate: float = 0.0,
    construction_years: float = 0.0,
    average_drawn_fraction: float = 0.55,
    financing_fees_pct: float = 0.01,
    developer_profit_pct_on_cost: float = 0.15,
    land_transaction_costs_pct: float = 0.0,
    asking_land_price: float | None = None,
) -> ResidualLandValueResult:
    """Static residual land value.

    ``deferral_years`` is the time from today until the stabilised value is
    realised (construction plus ramp-up); ``discount_rate`` brings it back to
    today. Financing cost = loan x rate x years x average drawn fraction plus
    arrangement fees, where loan = LTC x development cost excluding land.
    """
    for name, v in (("hard_costs", hard_costs), ("soft_costs", soft_costs), ("ffe_ose", ffe_ose), ("site_works", site_works),
                    ("preopening_working_capital", preopening_working_capital)):
        if v < 0:
            raise ValueError(f"{name} cannot be negative")
    if stabilised_value <= 0:
        raise ValueError("stabilised_value must be positive")
    if not 0 <= construction_ltc < 1:
        raise ValueError("construction_ltc must be between 0 and 1")
    if discount_rate < 0 or deferral_years < 0:
        raise ValueError("discount_rate and deferral_years cannot be negative")
    warnings: list[str] = []

    pv_value = stabilised_value / (1.0 + discount_rate) ** deferral_years
    contingency = contingency_pct_of_hard * (hard_costs + site_works)
    dev_cost = hard_costs + site_works + soft_costs + ffe_ose + preopening_working_capital + contingency
    loan = construction_ltc * dev_cost
    financing = loan * construction_interest_rate * construction_years * average_drawn_fraction + loan * financing_fees_pct
    profit = developer_profit_pct_on_cost * (dev_cost + financing)
    rlv = pv_value - dev_cost - financing - profit
    net_bid = rlv / (1.0 + land_transaction_costs_pct) if land_transaction_costs_pct else rlv
    if rlv <= 0:
        warnings.append("the residual is not positive: the scheme does not support any land payment at the required profit")
    headroom = poc = None
    if asking_land_price is not None:
        headroom = net_bid - asking_land_price
        total_cost = asking_land_price * (1.0 + land_transaction_costs_pct) + dev_cost + financing
        poc = (pv_value - total_cost) / total_cost if total_cost else None
        if headroom < 0:
            warnings.append(f"asking land price exceeds the residual by {-headroom:,.0f}; profit on cost at the asking price is {poc:.1%}")
    if dev_cost and pv_value / dev_cost < 1.15:
        warnings.append("present value of the stabilised asset is less than 1.15x development cost; margin for error is thin")
    return ResidualLandValueResult(
        stabilised_value=stabilised_value, deferral_years=deferral_years, discount_rate=discount_rate,
        present_value_of_stabilised_asset=pv_value, hard_costs=hard_costs, site_works=site_works, soft_costs=soft_costs,
        ffe_ose=ffe_ose, preopening_working_capital=preopening_working_capital, contingency=contingency,
        development_cost_ex_land_ex_finance=dev_cost, financing_costs=financing, developer_profit=profit,
        residual_land_value=rlv, land_transaction_costs_pct=land_transaction_costs_pct, max_land_bid_net_of_costs=net_bid,
        asking_land_price=asking_land_price, headroom_vs_asking=headroom, profit_on_cost_at_asking=poc, warnings=warnings,
    )
