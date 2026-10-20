# VT Capital Valuation Agent

A Claude-powered valuation analyst for VT Capital's deal team, backed by a deterministic
valuation engine. Claude handles the judgement (which methods apply, what the inputs imply,
what to pressure-test); the engine does every calculation so the numbers are reproducible
and testable.

## What it does

| Lens | Tools the agent calls | Engine module |
|---|---|---|
| Cost of capital | `compute_wacc`, `lever_beta` | `valuation/wacc.py` (CAPM with size, country and specific premia; Hamada levering) |
| DCF | `project_free_cash_flows`, `dcf_valuation`, `dcf_sensitivity` | `valuation/dcf.py`, `valuation/sensitivity.py` (unlevered FCF, mid-year convention, perpetuity and exit-multiple terminal values, implied-multiple and implied-growth cross-checks, two-way tables) |
| Relative value | `trading_comps`, `precedent_transactions` | `valuation/comps.py` (quartile statistics on EV/Revenue, EV/EBITDA, EV/EBIT and P/E; EV-to-equity bridge) |
| Returns | `lbo_returns`, `max_entry_multiple_for_target_irr` | `valuation/lbo.py` (annual debt paydown model, MOIC and IRR, ability-to-pay solver) |
| Synthesis | `build_football_field`, `financial_calculator` | `valuation/football_field.py`, `valuation/finance_math.py` |
| Hotel market study (RNAADR) | `hotel_market_study` | `valuation/hotel_market.py` (competitive set, HARC, demand by segment, fair share and penetration indices, latent and induced demand, new supply, occupancy, ADR and RevPAR by year) |
| Hotel forecast of revenue and expense (FIXVAR) | `hotel_fixvar_proforma` | `valuation/hotel_fixvar.py` (fixed and variable components with variability indices, USALI statement to NOI) |
| Hotel mortgage-equity valuation (HMEV) | `hotel_mortgage_equity_valuation` | `valuation/mortgage_equity.py` (loan sizing on LTV, DCR and debt yield, simultaneous valuation formula, equity residual) |
| Greenfield feasibility | `residual_land_value` | `valuation/residual.py` (stabilised value deferred less development, finance and profit) |
| Residential absorption | `residential_absorption` | `valuation/residential.py` (unit mix, pricing, absorption, payment plan, receipts by year) |
| Development DCF / FCFE | `development_cash_flow` | `valuation/development.py` (S-curve costs, construction debt, unlevered and equity returns, discounted residual land value) |
| Equity waterfall | `equity_waterfall` | `valuation/waterfall.py` (IRR hurdles, catch-up, promote, LP and GP returns) |

The agent operates under VT Capital's Institutional Standard Operating Procedure v2.0: for hotels and resorts it follows RNAADR to FIXVAR to HMEV to development appraisal to debt and equity underwriting (the three labels are VT Capital's working names for the methods; no HVS certification is asserted). The system prompt in `vt_valuation_agent/prompts.py` encodes the house process: derive the
WACC from its components, value with both terminal methods, triangulate against comps and
precedents, run sensitivities, apply sanity checks (terminal value share of EV, implied
multiples versus peers, growth versus GDP), and finish with a football field and the
assumptions to pressure-test. The agent has no market data feed: it works from the figures
you give it and labels any assumption it has to make.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=sk-ant-...      # or: ant auth login
```

Python 3.10 or newer. Default model is `claude-opus-5-5` at `high` effort; override with
`--model` / `--effort` or the `VT_VALUATION_MODEL` / `VT_VALUATION_EFFORT` environment variables.

## Use

One question, streamed answer:

```bash
vt-valuation-agent "Value a packaging company: LTM revenue 1.2bn, EBITDA 210m, growing 9% fading to 5% over five years, \
margins expanding from 18% to 20%. Net debt 220m, 48m shares. Peers trade at 8-11x EBITDA. \
Risk-free 4.2%, beta 1.15, ERP 5.5%, cost of debt 6.5%, tax 25%, 30% debt in the structure."
```

Attach files (notes, a CSV of peers, a JSON of assumptions) and save the answer:

```bash
vt-valuation-agent ask "Build a bid range for the attached target" --file notes.md --file peers.csv --save reports/target.md
```

Interactive session with follow-ups ("rerun at 9% WACC", "what could a sponsor pay for a 20% IRR?"):

```bash
vt-valuation-agent chat
```

Offline engine run from a JSON spec, no API key needed (useful for regression checks and
for seeing exactly what the tools compute):

```bash
vt-valuation-agent engine examples/sample_target.json
vt-valuation-agent engine examples/sample_target.json --json
```

Flags: `--show-thinking` streams summarised reasoning to stderr, `--quiet-tools` hides tool
progress, `--no-fallbacks` disables Anthropic's server-side refusal fallbacks (on by default).

## Use from Python

```python
from vt_valuation_agent import ValuationAgent

agent = ValuationAgent()                      # anthropic.Anthropic() from the environment
turn = agent.ask("Run a DCF on FCF of 100, 110, 121 at a 10% WACC with 2% terminal growth; net debt 100, 10m shares.")
print(turn.text)
for call in turn.tool_calls:
    print(call.name, call.output[:120])
follow_up = agent.ask("Now at 9% and 11%.")  # conversation is kept
```

The engine is importable on its own:

```python
from vt_valuation_agent.valuation import dcf_valuation, wacc, cost_of_equity_capm

ke = cost_of_equity_capm(risk_free_rate=0.042, beta=1.15, equity_risk_premium=0.055)
r = wacc(ke, pre_tax_cost_of_debt=0.065, tax_rate=0.25, debt_weight=0.30)
print(dcf_valuation([111, 127, 143, 159, 175], r.wacc, terminal_growth=0.025, mid_year=True, net_debt=220, shares_outstanding=48).value_per_share)
```

## How the agent is built

- `vt_valuation_agent/agent.py` runs the Anthropic SDK tool runner with streaming, an
  append-only message history (so follow-ups reuse earlier tool results and thinking blocks
  stay valid), a cached system prompt, `output_config.effort`, and `fallbacks: "default"`.
  Tools from a refused or truncated turn are never executed.
- `vt_valuation_agent/tools.py` defines the tools with `@beta_tool`; inputs are validated
  against the generated schema before a function runs, and bad inputs come back to the model
  as a tool error it can correct.
- `vt_valuation_agent/report.py` is the offline path that renders a markdown summary from a
  spec (see `examples/sample_target.json` for the format).

## Operating procedure

`docs/SOP_project_validation_and_IM.md` is the agent's implementation of the Institutional SOP v2.0 for
development and hospitality assets: reference tables (standards, data sources, KPI formulas,
benchmark ranges, tool coverage) and the phase-by-phase process from intake through market
validation, residual land value, financial modelling, validation gates, IM assembly, teaser and
outreach, trainee mentorship and quality control.

## Conventions

- Rates are decimals (`0.095` is 9.5%); money is in one consistent unit, usually millions.
- Mid-year convention is on by default. The perpetuity terminal value is discounted over
  `n - 0.5` periods; the exit-multiple terminal value over `n` full periods.
- Taxes in the FCF projection are charged on EBIT. Net working capital is a share of revenue
  and only the change hits cash flow.
- The LBO is a single-tranche annual model with a cash sweep; it is for returns
  triangulation, not a financing model.
- The mortgage-equity valuation uses monthly-pay mortgage constants, a ten-year hold by default,
  and takes the most restrictive of the LTV, DCR and debt-yield loans as the lender's loan.
- FIXVAR variability indices are computed in real terms (projected revenue deflated by the
  inflation factor over base revenue), so inflation does not inflate the variable component twice.

## Tests

```bash
pytest
```

Covers the engine against hand calculations, the tool schemas and JSON-input execution
path, the agent's request construction (no network), and an end-to-end engine run on the
sample spec.

## Disclaimer

Output is analytical support for VT Capital's internal decision-making. It is not
investment advice, a fairness opinion, or a substitute for the deal team's own diligence.
