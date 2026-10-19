"""Deterministic valuation engine used by the VT Capital valuation agent.

Everything in this package is plain Python with no network access, so the
numbers the agent reports are reproducible and testable.
"""

from .comps import Comparable, CompsResult, TargetMetrics, relative_valuation
from .dcf import DcfResult, ProjectionYear, dcf_valuation, project_free_cash_flows
from .finance_math import cagr, irr, npv
from .football_field import FootballField, ValuationRange, football_field
from .lbo import LboResult, lbo_returns, max_entry_multiple_for_irr
from .sensitivity import SensitivityTable, dcf_sensitivity
from .wacc import WaccResult, cost_of_equity_capm, relever_beta, unlever_beta, wacc

__all__ = [
    "Comparable",
    "CompsResult",
    "DcfResult",
    "FootballField",
    "LboResult",
    "ProjectionYear",
    "SensitivityTable",
    "TargetMetrics",
    "ValuationRange",
    "WaccResult",
    "cagr",
    "cost_of_equity_capm",
    "dcf_sensitivity",
    "dcf_valuation",
    "football_field",
    "irr",
    "lbo_returns",
    "max_entry_multiple_for_irr",
    "npv",
    "project_free_cash_flows",
    "relative_valuation",
    "relever_beta",
    "unlever_beta",
    "wacc",
]
