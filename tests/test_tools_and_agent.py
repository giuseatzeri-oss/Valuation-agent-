import json

import anthropic
import pytest
from anthropic.lib.tools import ToolError

from vt_valuation_agent import tools
from vt_valuation_agent.agent import ValuationAgent
from vt_valuation_agent.report import load_spec, render_markdown, run_engine

EXPECTED_TOOLS = {
    "compute_wacc", "lever_beta", "project_free_cash_flows", "dcf_valuation", "dcf_sensitivity",
    "trading_comps", "precedent_transactions", "lbo_returns", "max_entry_multiple_for_target_irr",
    "build_football_field", "financial_calculator",
    "hotel_market_study", "hotel_fixvar_proforma", "hotel_mortgage_equity_valuation", "residual_land_value",
    "residential_absorption", "development_cash_flow", "equity_waterfall",
}


def test_tool_schemas_are_well_formed():
    names = set()
    for tool in tools.VALUATION_TOOLS:
        d = tool.to_dict()
        names.add(d["name"])
        assert d["description"]
        assert d["input_schema"]["type"] == "object"
        assert d["input_schema"].get("additionalProperties") is False
        assert d.get("eager_input_streaming") is True
    assert names == EXPECTED_TOOLS


def test_tools_run_from_json_input_like_the_runner():
    out = json.loads(tools.compute_wacc.call({"risk_free_rate": 0.04, "beta": 1.0, "equity_risk_premium": 0.05,
                                              "pre_tax_cost_of_debt": 0.06, "tax_rate": 0.25, "debt_weight": 0.3}))
    assert out["wacc"] == pytest.approx(0.7 * 0.09 + 0.3 * 0.045)

    dcf = json.loads(tools.dcf_valuation.call({"free_cash_flows": [100, 110, 121], "discount_rate": 0.1,
                                               "terminal_growth": 0.02, "mid_year": False, "net_debt": 100,
                                               "shares_outstanding": 10}))
    assert dcf["enterprise_value"] == pytest.approx(272.727 + 1542.75 / 1.331, rel=1e-4)

    comps = json.loads(tools.trading_comps.call({
        "peers": [{"name": "A", "ev_ebitda": 8}, {"name": "B", "ev_ebitda": 10}, {"name": "C", "ev_ebitda": 12}],
        "target": {"ebitda": 100}, "net_debt": 200, "shares_outstanding": 10,
    }))
    assert comps["implied"][0]["mid"]["value_per_share"] == pytest.approx(80)

    ff = json.loads(tools.build_football_field.call({
        "ranges": [{"method": "DCF", "low": 900, "high": 1100}, {"method": "Comps", "low": 800, "high": 1000}],
        "net_debt": 100, "shares_outstanding": 10,
    }))
    assert ff["weighted_mid"]["enterprise"] == pytest.approx(950)

    calc = json.loads(tools.financial_calculator.call({"operation": "irr", "cash_flows": [-100, 0, 121]}))
    assert calc["result"] == pytest.approx(0.10, abs=1e-6)


def test_tool_errors_are_reported_not_raised_as_stack_traces():
    with pytest.raises(ToolError):
        tools.dcf_valuation.call({"free_cash_flows": [1, 2], "discount_rate": 0.05, "terminal_growth": 0.06})
    with pytest.raises(ToolError):
        tools.lever_beta.call({"beta": 1.0, "debt_to_equity": 0.5, "tax_rate": 0.25, "direction": "sideways"})


def test_agent_builds_cacheable_request_without_network():
    agent = ValuationAgent(client=anthropic.Anthropic(api_key="test-key"), effort="xhigh")
    params = agent._request_params()
    assert params["model"] == "claude-opus-5-5"
    assert params["max_tokens"] >= 64000
    assert params["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert params["output_config"] == {"effort": "xhigh"}
    assert params["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in params["betas"]
    assert params["stream"] is True
    assert "thinking" not in params
    assert len(params["tools"]) == len(EXPECTED_TOOLS)
    with pytest.raises(ValueError):
        ValuationAgent(client=anthropic.Anthropic(api_key="test-key"), effort="extreme")
    with pytest.raises(ValueError):
        agent.ask("   ")


def test_engine_runs_sample_spec_end_to_end():
    spec = load_spec("examples/sample_target.json")
    results = run_engine(spec)
    assert 0.08 < results["wacc"].wacc < 0.13
    assert results["dcf_perpetuity"].enterprise_value > 0
    assert results["dcf_exit_multiple"].enterprise_value > 0
    assert results["football_field"].weighted_mid["enterprise"] > 0
    md = render_markdown(results)
    for heading in ("Cost of capital", "DCF", "Sensitivity", "Trading comparables", "Precedent transactions", "Football field"):
        assert heading in md
