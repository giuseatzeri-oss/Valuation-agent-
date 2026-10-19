"""Run the valuation engine from a JSON spec without calling Claude.

This is the offline path: ``vt-valuation-agent engine spec.json`` renders a
markdown valuation summary (WACC, DCF both ways, sensitivity, comps,
precedents, football field) straight from the deterministic engine. It is
useful for regression checks and for users without an API key.
"""

from __future__ import annotations

import json
from pathlib import Path

from .valuation import (
    Comparable,
    TargetMetrics,
    ValuationRange,
    cost_of_equity_capm,
    dcf_sensitivity,
    dcf_valuation,
    football_field,
    project_free_cash_flows,
    relative_valuation,
    wacc,
)


def load_spec(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def run_engine(spec: dict) -> dict:
    """Execute every method the spec has inputs for and return raw results."""
    out: dict = {"company": spec.get("company", "Target"), "units": spec.get("currency_unit", "")}
    net_debt = float(spec.get("net_debt", 0.0))
    shares = spec.get("shares_outstanding")
    out["net_debt"], out["shares_outstanding"] = net_debt, shares

    w = spec["wacc"]
    ke = cost_of_equity_capm(
        w["risk_free_rate"], w["beta"], w["equity_risk_premium"],
        w.get("size_premium", 0.0), w.get("country_risk_premium", 0.0), w.get("company_specific_premium", 0.0),
    )
    wres = wacc(ke, w["pre_tax_cost_of_debt"], w["tax_rate"], w.get("equity_value"), w.get("debt_value"), w.get("debt_weight"))
    out["wacc"] = wres

    p = spec["projection"]
    schedule = project_free_cash_flows(
        p["base_revenue"], p["revenue_growth"], p["ebitda_margin"], p["da_pct_revenue"],
        p["capex_pct_revenue"], p["nwc_pct_revenue"], p["tax_rate"], p.get("base_nwc"),
    )
    out["projection"] = schedule
    fcfs = [y.unlevered_fcf for y in schedule]
    terminal_ebitda = schedule[-1].ebitda
    mid_year = bool(spec.get("mid_year", True))

    t = spec.get("terminal", {})
    ranges: list[ValuationRange] = []
    if "growth" in t:
        res = dcf_valuation(fcfs, wres.wacc, terminal_growth=t["growth"], terminal_metric=terminal_ebitda,
                            mid_year=mid_year, net_debt=net_debt, shares_outstanding=shares)
        out["dcf_perpetuity"] = res
    if "exit_multiple" in t:
        res = dcf_valuation(fcfs, wres.wacc, exit_multiple=t["exit_multiple"], terminal_metric=terminal_ebitda,
                            mid_year=mid_year, net_debt=net_debt, shares_outstanding=shares)
        out["dcf_exit_multiple"] = res

    s = spec.get("sensitivity")
    if s:
        table = dcf_sensitivity(
            fcfs, s["discount_rates"], s.get("terminal_growth_rates"), s.get("exit_multiples"),
            terminal_metric=terminal_ebitda, output=s.get("output", "enterprise_value"),
            mid_year=mid_year, net_debt=net_debt, shares_outstanding=shares,
        )
        out["sensitivity"] = table
        # DCF range from the sensitivity grid's interior (drop the extreme corners)
        cells = sorted(v for row in table.values for v in row if v is not None)
        if len(cells) >= 4 and table.output == "enterprise_value":
            trim = max(1, len(cells) // 8)
            ranges.append(ValuationRange(method=f"DCF ({table.column_label} sensitivity)", low=cells[trim], high=cells[-trim - 1], basis="enterprise", weight=2.0))
    elif "dcf_perpetuity" in out and "dcf_exit_multiple" in out:
        evs = sorted([out["dcf_perpetuity"].enterprise_value, out["dcf_exit_multiple"].enterprise_value])
        ranges.append(ValuationRange(method="DCF (perpetuity to exit multiple)", low=evs[0], high=evs[1], basis="enterprise", weight=2.0))

    target = TargetMetrics(**spec.get("target_metrics", {}))
    if target.ebitda is None:
        target.ebitda = spec.get("ltm_ebitda")
    for key, kind, label in (("trading_comps", "trading_comps", "Trading comps"), ("precedent_transactions", "precedent_transactions", "Precedent transactions")):
        rows = spec.get(key)
        if not rows:
            continue
        comps = [Comparable(**r) for r in rows]
        res = relative_valuation(comps, target, net_debt, shares, kind)
        out[key] = res
        for imp in res.implied:
            ranges.append(ValuationRange(
                method=f"{label} {imp.multiple.upper().replace('_', '/')}",
                low=imp.low["enterprise_value"], mid=imp.mid["enterprise_value"], high=imp.high["enterprise_value"],
                basis="enterprise", weight=1.0,
            ))
    if ranges:
        out["football_field"] = football_field(ranges, net_debt, shares)
    return out


def render_markdown(results: dict) -> str:
    units = results.get("units") or "units"
    lines = [f"# {results['company']} - valuation summary", "", f"_All amounts in {units}; engine output, no market data feed._", ""]

    w = results["wacc"]
    lines += ["## Cost of capital", "", "| Component | Value |", "|---|---|",
              f"| Cost of equity | {w.cost_of_equity:.2%} |", f"| Pre-tax cost of debt | {w.pre_tax_cost_of_debt:.2%} |",
              f"| After-tax cost of debt | {w.after_tax_cost_of_debt:.2%} |", f"| Debt weight | {w.debt_weight:.1%} |",
              f"| **WACC** | **{w.wacc:.2%}** |", ""]

    sched = results["projection"]
    lines += ["## Projected unlevered free cash flow", "", "| Year | Revenue | EBITDA | EBIT | Taxes | Capex | dNWC | UFCF |", "|---|---|---|---|---|---|---|---|"]
    for y in sched:
        lines.append(f"| {y.year} | {y.revenue:,.1f} | {y.ebitda:,.1f} | {y.ebit:,.1f} | {y.taxes:,.1f} | {y.capex:,.1f} | {y.change_in_nwc:,.1f} | {y.unlevered_fcf:,.1f} |")
    lines.append("")

    lines += ["## DCF", "", "| Case | Terminal value | TV % of EV | Enterprise value | Equity value | Per share | Cross-check |", "|---|---|---|---|---|---|---|"]
    for key, label in (("dcf_perpetuity", "Perpetuity growth"), ("dcf_exit_multiple", "Exit multiple")):
        r = results.get(key)
        if not r:
            continue
        cross = (f"implied exit multiple {r.implied_exit_multiple:.1f}x" if r.implied_exit_multiple is not None
                 else f"implied growth {r.implied_terminal_growth:.2%}" if r.implied_terminal_growth is not None else "")
        ps = f"{r.value_per_share:,.2f}" if r.value_per_share is not None else "n/a"
        lines.append(f"| {label} | {r.terminal_value:,.1f} | {r.terminal_value_pct_of_ev:.0%} | {r.enterprise_value:,.1f} | {r.equity_value:,.1f} | {ps} | {cross} |")
    warnings = sorted({wn for k in ("dcf_perpetuity", "dcf_exit_multiple") if results.get(k) for wn in results[k].warnings})
    if warnings:
        lines += [""] + [f"- Warning: {wn}" for wn in warnings]
    lines.append("")

    if results.get("sensitivity"):
        t = results["sensitivity"]
        lines += [f"## Sensitivity ({t.output.replace('_', ' ')})", "", t.to_markdown("{:,.2f}" if t.output == "value_per_share" else "{:,.1f}"), ""]

    for key, label in (("trading_comps", "Trading comparables"), ("precedent_transactions", "Precedent transactions")):
        res = results.get(key)
        if not res:
            continue
        lines += [f"## {label}", "", "| Multiple | n | Q1 | Median | Mean | Q3 |", "|---|---|---|---|---|---|"]
        for st in res.statistics:
            lines.append(f"| {st.multiple} | {st.n} | {st.first_quartile:.1f}x | {st.median:.1f}x | {st.mean:.1f}x | {st.third_quartile:.1f}x |")
        lines += ["", "| Implied from | Target metric | EV low (Q1) | EV mid (median) | EV high (Q3) |", "|---|---|---|---|---|"]
        for imp in res.implied:
            lines.append(f"| {imp.multiple} | {imp.target_metric:,.1f} | {imp.low['enterprise_value']:,.1f} | {imp.mid['enterprise_value']:,.1f} | {imp.high['enterprise_value']:,.1f} |")
        for note in res.notes:
            lines.append(f"- Note: {note}")
        lines.append("")

    ff = results.get("football_field")
    if ff:
        lines += ["## Football field (enterprise value)", "", "| Method | Low | Mid | High | Weight |", "|---|---|---|---|---|"]
        for b in ff.bars:
            lines.append(f"| {b.method} | {b.enterprise_low:,.1f} | {b.enterprise_mid:,.1f} | {b.enterprise_high:,.1f} | {b.weight:g} |")
        lines += ["", f"- Overall range: {ff.overall_low['enterprise']:,.1f} to {ff.overall_high['enterprise']:,.1f}",
                  f"- Weighted central value: {ff.weighted_mid['enterprise']:,.1f} (median of methods {ff.median_mid['enterprise']:,.1f})",
                  f"- Equity value at central: {ff.weighted_mid['equity']:,.1f}"]
        if ff.weighted_mid.get("per_share") is not None:
            lines.append(f"- Per share at central: {ff.weighted_mid['per_share']:,.2f}")
        for note in ff.notes:
            lines.append(f"- Note: {note}")
        lines.append("")
    lines.append("_Analytical support for VT Capital's internal use; not investment advice._")
    return "\n".join(lines)
