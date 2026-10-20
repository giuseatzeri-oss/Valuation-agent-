# Agent Operating Procedure: Project Validation, Feasibility, Valuation and Investment Memoranda

**To:** VT Capital Asset Management Investment Committee, Investment Team and AI Agents
**From:** VT Capital Valuation Agent (operating procedure)
**Date:** 20 October 2026
**Subject:** How the agent executes the Institutional Standard Operating Procedure v2.0 (21 October 2026): reference tables, tool coverage and the step-by-step procedure for each SOP

This document is the agent's implementation of VT Capital Asset Management's Institutional Standard Operating Procedure v2.0 ("the SOP"). Where the two differ, the SOP governs and this document is corrected. Part A holds the reference tables: the master methodology table with the agent tool that executes each method, the external frameworks and data sources, the formulas, the asset-class drivers, the validation controls, the agent roles and the evidence grades. Part B walks through SOP 01 to SOP 11 and states what the agent does at each step, with which tool, and what it will not do without a human.

Core workflow: Origination, Screening, RNAADR market research, FIXVAR operating forecast, HMEV / DCF valuation, Development appraisal, Debt and equity underwriting, Risk validation, Investment Committee, IM, Investor outreach.

Methodology note, carried over from the SOP: RNAADR, FIXVAR and HMEV are working labels for the analytical approaches VT Capital describes. The agent's tools implement those approaches from first principles. Equivalence to specific proprietary HVS workbooks is not independently verified and the agent does not assert HVS certification. The Advanced Concepts workbook and any proprietary RNAADR, FIXVAR or HMEV files have not been audited; week 1 of the roadmap covers that.

Every benchmark range in this document is an indicative starting point for the assumptions log, graded C (estimated) until replaced with a project-specific, dated, sourced figure.

---

## Part A. Reference tables

### A1. Master methodology reference table and agent tool coverage

| Ref. | Method | Principal output | Agent tool | Status |
|---|---|---|---|---|
| M01 | RNAADR | Room-night demand, occupancy, ADR | `hotel_market_study` | Available |
| M02 | Competitive penetration | Market share versus fair share | `hotel_market_study` (base-year table and projected subject penetration) | Available |
| M03 | Latent demand | Unaccommodated and induced demand | `hotel_market_study` (`unaccommodated_demand`, `induced_demand`) | Available |
| M04 | FIXVAR | Ten-year operating P&L | `hotel_fixvar_proforma` | Available |
| M05 | USALI framework | Consistent hospitality classifications | Line structure of `hotel_fixvar_proforma` (departmental, undistributed, management fees, fixed charges, reserve) | Available |
| M06 | HMEV | Mortgage-equity property value | `hotel_mortgage_equity_valuation`; cross-checked with `dcf_valuation` and `compute_wacc` | Available |
| M07 | Debt sizing | LTV, DSCR and debt yield constraints | `hotel_mortgage_equity_valuation` (minimum of the three governs) | Available |
| M08 | Residual Land Value | Maximum supportable land price | `residual_land_value` (preliminary) and `development_cash_flow` (discounted, from dated cash flows) | Available |
| M09 | Development DCF / FCFE | NPV, project and equity IRR | `development_cash_flow` | Available |
| M10 | Equity waterfall | JV distributions and sponsor promote | `equity_waterfall` | Available |
| M11 | Residential absorption | Sales pace and cash receipts | `residential_absorption` | Available |
| M12 | Scenario analysis | Downside, base and upside | `dcf_sensitivity` plus re-runs of the chain under each case; `build_football_field` | Available |
| M13 | Investment committee | Decision and conditions | Agent drafts the committee memorandum; decision is human | Human |
| M14 | IM, teaser and data room | Investor deliverables | Agent drafts; human approval before external distribution | Human-gated |
| Support | Cost of capital, relative value, acquisition returns, calculator | WACC, comps, precedents, LBO, NPV / IRR | `compute_wacc`, `lever_beta`, `project_free_cash_flows`, `trading_comps`, `precedent_transactions`, `lbo_returns`, `max_entry_multiple_for_target_irr`, `financial_calculator` | Available |

### A2. External reference frameworks and data sources

Reference sources are recorded with dates and reliability ratings in the source register.

| Area | Reference | How the agent uses it |
|---|---|---|
| Hotel market and valuation methodology | HVS published methodologies (subject to licensing); Rushmore and Baum, *Hotels and Motels: Valuations and Market Studies* (Appraisal Institute) | Built-up demand analysis, fixed and variable forecasting, mortgage-equity technique, as working labels only |
| Hotel accounting | USALI (HFTP and AHLA, current edition) | Departmental and undistributed classifications, GOP, management fees, fixed charges, reserve, NOI |
| Valuation standards | RICS Valuation Global Standards (Red Book), IVS, RICS *Valuation of development property* | Bases of value, assumptions and special assumptions, residual method structure and risk disclosure |
| Hotel benchmarks | STR / CoStar comp-set reports, HotStats | Occupancy, ADR, RevPAR, segmentation, seasonality, operating ratios |
| Tourism and macro | Local tourism statistics (ISTAT, Saudi Tourism Authority and GASTAT, UAE DET and DCT, VisitBritain and ONS), UN Tourism, airport traffic statistics, central banks and the IMF | Demand growth by segment and feeder market, inflation, risk-free rates |
| Transactions and yields | Comparable transactions (MSCI Real Capital Analytics, broker deal lists, announcements), broker investment outlooks | Terminal and going-in cap rates, value per key, precedent EV / EBITDA |
| Costs | Contractor quotations and quantity surveyor cost plans; Turner and Townsend and Arcadis cost surveys | Hard, site and soft costs per sqm and per key |
| Debt | Bank term sheets and lender soundings | Interest rate, amortisation, maturity, maximum LTV, minimum DSCR, minimum debt yield, fees, covenants |
| Residential | Notarial and cadastral records, developer price lists, sold-out timelines, branded residences research | Achieved price per sqm, absorption, branded premium |
| Regulation | Local planning and coastal law; securities marketing rules in each jurisdiction | Buildability; whether placement, introductions or transaction-linked remuneration are regulated activities |

### A3. Formulas (as stated in the SOP, with the tool fields that implement them)

| Quantity | Formula | Tool implementation |
|---|---|---|
| Effective rooms | Rooms x competitive weight | `Competitor.rooms x competitive_weight` (and `fraction_open` for HARC) |
| HARC | Rooms x days open / days in year | `rooms x fraction_open` |
| Accommodated room nights | Rooms x days open x occupancy | `HARC x 365 x occupancy` |
| Segment room nights | Accommodated room nights x segment share | `segmentation` shares (sum to 1) |
| Fair share | Effective available room nights / total effective available room nights | `fair_share` per competitor and `subject_fair_share` per year |
| Market share | Room nights captured / total market room nights | `market_share`, `subject_market_share` |
| Penetration index | Market share / fair share | `penetration_by_segment` (base year); `SubjectHotel.penetration` per segment per year (projected) |
| Blended ADR | Sum(segment room nights x segment ADR) / total room nights | `subject_adr` from `segment_adr` and `subject_room_nights_by_segment` |
| RevPAR | ADR x occupancy | `subject_revpar` |
| FIXVAR line | Inflated fixed base + inflated variable base x (forecast utilisation / base utilisation) | `base_amount x inflation x (fixed_pct + (1 - fixed_pct) x index ratio)`; index is occupancy, department revenue or total revenue, measured in real terms |
| Debt by LTV | Property value x maximum LTV | `loan_to_value` (solved simultaneously with value) |
| Debt by DSCR | NOI / (minimum DSCR x debt constant) | `debt_coverage_ratio`, `mortgage_constant`, `sizing_year` |
| Debt by yield | NOI / minimum debt yield | `debt_yield` |
| Maximum debt | Minimum of the three constraints | `binding_constraint`, `loan` |
| Annual equity cash flow | Property cash flow less debt service less applicable additional costs | `equity_cash_flows` |
| Terminal value | Year-11 NOI / terminal capitalisation rate | `reversion_gross` from `net_income[n]` |
| Net sale proceeds | Terminal value less selling costs less outstanding debt | `reversion_net`, `loan_balance_at_reversion`, `equity_residual` |
| Mortgage-equity value | Initial mortgage balance + PV of equity cash flows and equity reversion at the equity yield | `value` (closed-form simultaneous solution for LTV; direct for DSCR and debt yield) |
| Preliminary RLV | Completed development value less development costs less financing costs less required developer profit | `residual_land_value` with deferral of the completed value |
| Discounted RLV | Land payment at which the dated project cash flow earns the required project return | `development_cash_flow.discounted_residual_land_value` |
| Unlevered IRR, NPV | From dated project cash flows before debt | `unlevered_irr`, `unlevered_npv_at_hurdle` |
| Equity IRR, multiple, payback | From equity cash flows after construction debt | `equity_irr`, `equity_multiple`, `equity_payback_year` |
| Waterfall tier | Distributions to capital until the hurdle IRR is met, remainder as promote; optional catch-up to a target promote share | `WaterfallTier(hurdle_irr, capital_share)`, `catch_up_pct`, `catch_up_to_promote` |

Worked examples from the SOP that the agent's test suite reproduces: 120 rooms open 300 days at 65 percent give 23,400 accommodated room nights and, at a 60 percent leisure share, 14,040 leisure room nights; a EUR 1.0m base rooms expense, 60 percent fixed, with occupancy rising from 70 to 80 percent gives EUR 600,000 fixed plus EUR 457,143 variable, EUR 1,057,143 before inflation.

### A4. Asset-specific underwriting drivers (SOP 06)

| Asset class | Critical drivers | Agent approach |
|---|---|---|
| Urban hotel | Corporate demand, ADR, occupancy | RNAADR with commercial and meeting segments weighted; FIXVAR; HMEV |
| Luxury resort / glamping | Seasonality, ADR, infrastructure, utilisation | RNAADR with leisure and group segments and a seasonality check; infrastructure in `development_cash_flow` cost items |
| Branded residences / condo hotel | Sale price, absorption, brand fees, rental structure | `residential_absorption` with brand fee; rental pool income as other income |
| Wellness / longevity spa | Treatment utilisation, staffing, equipment, memberships | FIXVAR revenue line driven by treatments x yield; expense index on department revenue |
| Golf resort | Rounds, membership, course maintenance | FIXVAR revenue line driven by rounds and memberships; maintenance as a largely fixed expense |
| Houseboat | Fleet utilisation, mooring, maintenance | Unit-based occupancy model analogous to rooms; mooring and maintenance fixed |
| Restaurant | Covers, spend, food and labour costs | Covers x average spend; food cost variable, labour partly fixed |
| Heritage hotel | Conversion costs and preservation constraints | Cost items with contingency; constraints register in screening |
| Serviced apartments | Length of stay, occupancy, operating cost | RNAADR with extended-stay segment; lower departmental cost base |

Mixed-use components are underwritten individually, then consolidated. Hotel room-night models are not applied mechanically to non-lodging assets.

### A5. Validation controls (SOP 09) and evidence grades

| Control | Pass condition | Agent check |
|---|---|---|
| Demand and occupancy | Demand balances; occupancy 0 to 100 percent | Allocated room nights reconcile to market demand and inventory; tool warnings above 80 percent occupancy and 1.3x penetration resolved |
| ADR and room revenue | Benchmarked and arithmetically reconciled | Rooms revenue equals room nights x ADR; ADR index evidenced against the comp set |
| Expenses and EBITDA | Cost drivers and P&L reconcile | Every FIXVAR line has a stated driver, fixed share and source; GOP and NOI margins inside comp-set ranges |
| Debt | Balances, fees, service and covenants reconcile | Minimum of LTV, DSCR and debt yield governs; debt service covered in every year; `development_cash_flow` balance returns to zero at exit |
| Exit | Forward NOI, cap rate, costs and debt consistent | Terminal rate above going-in unless justified; net proceeds after selling costs and outstanding debt |
| Returns | IRR and multiple reconcile to cash flows | HMEV `equity_irr_check` equals the equity yield; unlevered DCF within a defensible band of the HMEV value |
| Development | Costs, timing and RLV consistent | Preliminary and discounted residuals reconciled, differences explained by timing |
| Sources and uses | Funding sources equal uses | Land plus costs plus finance equals equity plus debt in every period |

Evidence grades: A verified, B corroborated, C estimated, D unverified. Material D-grade assumptions block unconditional investment approval. The agent maintains the source register, the assumptions log and the version history; the independent reviewer signs off.

### A6. Agent roles and the human approval boundary (SOP 10)

| Agent role | Output | Tools the role uses |
|---|---|---|
| Chief Strategy Officer | Investment priorities | None (judgement and screening criteria) |
| Chief Development Officer | Origination pipeline | Project register (SOP 01) |
| Market Intelligence | RNAADR and market feasibility | `hotel_market_study` |
| Hospitality Operations | FIXVAR and operating projections | `hotel_fixvar_proforma`, `project_free_cash_flows` for non-hotel components |
| Valuation | HMEV, DCF and value reconciliation | `hotel_mortgage_equity_valuation`, `compute_wacc`, `lever_beta`, `dcf_valuation`, `trading_comps`, `precedent_transactions` |
| Development | CAPEX, phasing and RLV | `residual_land_value`, `development_cash_flow`, `residential_absorption` |
| Debt Advisory | Debt sizing and financing terms | `hotel_mortgage_equity_valuation` sizing, `development_cash_flow` financing, `lbo_returns` |
| Chief Investment Officer | Integrated underwriting model | All of the above; `dcf_sensitivity`, `build_football_field` |
| Chief Risk Officer | Independent validation | Re-runs with independent inputs; validation controls in A5 |
| Legal and Compliance | Regulatory and document checks | None; flags items for human counsel |
| Capital Markets | IM and investment teaser | Drafting from the approved model version |
| Investor Relations | Investor matching and correspondence | Drafting; sending is human |
| Training | Annotated models and case studies | Annotation of every tool call and assumption |

Human approval is required for final investment recommendations, legal opinions, regulatory determinations, contractual commitments and external distribution.

### A7. Indicative benchmark ranges for the assumptions log (grade C until replaced)

| Assumption | Indicative range | Replace with |
|---|---|---|
| Hotel ramp-up to stabilisation | 3 to 4 operating years | Operator underwriting, comp-set opening histories |
| Stabilised occupancy, seasonal luxury resort | 55 to 70 percent annual | STR comp set and seasonality calendar |
| ADR index for new branded luxury supply | 1.10 to 1.30 of the segment | Paired comparables, operator pipeline |
| Branded residence price premium | 20 to 35 percent over unbranded | Paired transactions, branded residences research |
| Brand licence fee on residential sales | 3 to 5 percent | Residential licence term sheet |
| Rooms expense split | 50 to 70 percent fixed, 30 to 50 percent variable with occupancy | Comparable statements, HotStats |
| Replacement reserve | 4 percent of revenue is illustrative only; asset-specific | Hotel management agreement |
| Hotel debt terms | 20 to 25 year amortisation, LTV 55 to 65 percent, DSCR 1.30x to 1.50x, debt yield 9 to 11 percent | Bank term sheets |
| Terminal capitalisation rate | Going-in plus 50 to 100 basis points over a ten-year hold | Transaction evidence |
| Soft costs; contingency | 12 to 20 percent of hard costs; 5 to 10 percent of hard and site costs | Fee proposals; quantity surveyor's risk register |
| Developer profit | 15 to 20 percent on cost | Investment committee return policy |
| Equity yield | Asset and market specific; test a 200 basis point band | Investor surveys, recent raises |

---

## Part B. The agent's procedure, SOP by SOP

### SOP 01. Project intake and screening (owner: Chief Development Officer agent)

1. Register the project with a unique ID, legal owner, site location, title, planning status, asset class, development concept, indicative investment requirement, sponsor, project stage, responsible human manager and source documents.
2. Open the source register (document, date, author, reliability rating) and the assumptions log (value, unit, source, grade A to D, rationale, owner, sensitivity tested).
3. Fix conventions: currency and unit, measurement basis (GFA, NSA, keys), valuation date, nominal versus real, tax treatment.
4. Record the stage and what it needs: A Screening (preliminary opportunity assessment), B Feasibility (market, title and planning investigation), C Underwriting (integrated model and financing analysis), D Committee (independent risk and model review), E Investor-ready (approved IM and controlled data room), F Execution (investor process, documentation and closing).
5. Gate: no project advances to investor-ready status with unresolved critical ownership, planning, environmental or financial evidence gaps. The agent lists the open gaps at every stage transition.

### SOP 02. RNAADR market research (owner: Market Intelligence agent)

Tool: `hotel_market_study`.

1. **Define the primary market area** using accessibility, feeder markets, demand generators, product positioning, seasonality and competing destinations. Identify primary and secondary competitors; secondary properties receive documented competitive weights.
2. **Supply, historic room counts and demand.** Enter each competitor's rooms, days open (as a fraction of the year, giving HARC), occupancy and segmentation into commercial, meetings and conventions, leisure and, when material, other or contracted business. Use actual inventory dates where supply changes within a year. The tool returns effective rooms, HARC-based accommodated room nights, segment room nights, fair share, market share and penetration index per competitor.
3. **Latent demand and market growth.** Enter unaccommodated demand (capacity constraints) and induced demand (new generators) separately, with sources, and never double count new tourism attractions or hotel-generated demand. Enter organic demand growth and competing supply by segment.
4. **Competitive penetration.** Estimate the subject's penetration per segment per year from brand, location, amenities, distribution, management quality and stabilisation. The tool normalises shares each year so that allocated demand reconciles to forecast market demand and available inventory.
5. **ADR and RevPAR.** Enter market ADR by segment with market-supported rate positioning for the subject and explicit nominal inflation. Public rack rates are not realised ADR. The tool blends segment ADRs by the subject's mix.
6. **Deliverables.** Supply database, competitive-set weights, demand segmentation, historic demand, latent demand, supply additions, penetration indices, occupancy, ADR and RevPAR forecasts, all drawn from the tool output and the source register.

### SOP 03. FIXVAR ten-year operating model (owner: Hospitality Operations / Financial Modelling agent)

Tool: `hotel_fixvar_proforma`, with the RNAADR occupancy and ADR series.

1. **Base statement.** Establish an actual, normalised or synthetic base-year statement and identify the origin of every input. Use USALI-aligned departmental classifications.
2. **Drivers by revenue centre.** Rooms: occupied room nights x ADR. Food and beverage: covers x average spend. Spa and wellness: treatments x average yield. Golf: rounds and memberships. Events: events x revenue per event. Other departments: the relevant activity-specific utilisation. Non-rooms departments enter as revenue lines with their own fixed share; where a department's driver is not occupancy, its base amount is built from the driver outside the tool and its variable component follows the department's own revenue.
3. **Fixed and variable components.** Forecast expense = inflated fixed base + inflated variable base x (forecast utilisation / base utilisation). Select the correct cost driver per department rather than applying occupancy universally. Fixed and variable proportions are assumptions to be benchmarked, not universal rules.
4. **Coverage.** Rooms, F&B, spa, golf and other departmental expenses; administrative and general; sales and marketing; maintenance; utilities; IT; management fees; insurance; taxes; ground rent; replacement reserves. The 4 percent revenue reserve is illustrative only and must be asset-specific.
5. **Outputs.** Ten-year P&L, departmental contribution, GOP, EBITDA, a consistently defined NOI / valuation cash flow, replacement reserves and sensitivities. Distinguish accounting earnings from distributable cash flow.

### SOP 04. HMEV mortgage-equity valuation (owner: Valuation agent)

Tool: `hotel_mortgage_equity_valuation`, with the FIXVAR NOI for the holding period plus one year.

1. **Debt underwriting criteria.** Current market interest rates, amortisation, maturity, maximum LTV, minimum DSCR, minimum debt yield, fees, covenants, equity yield and holding period, from term sheets and lender soundings.
2. **Debt sizing.** Debt by LTV = value x maximum LTV; by DSCR = NOI / (minimum DSCR x debt constant); by yield = NOI / minimum debt yield. Maximum debt is the minimum of the three, subject to additional lender tests. The DSCR and debt-yield tests use year-one NOI by default; set the sizing year to the first stabilised year when the lender sizes on stabilised income and say so.
3. **Equity cash flow and reversion.** Annual equity cash flow = property cash flow less debt service less applicable additional costs and contributions. Year-10 terminal value = year-11 NOI / terminal capitalisation rate. Net sale proceeds = terminal value less selling costs less outstanding debt.
4. **Value.** Mortgage-equity value = initial mortgage balance + present value of equity cash flows and equity reversion at the required equity yield. Because the LTV loan depends on value, the tool solves the simultaneous formula in closed form (equivalent to iterating to convergence) and reports an IRR check equal to the equity yield.
5. **Cross-check.** Independently against an unlevered DCF (`compute_wacc`, `dcf_valuation`) and comparable transactions (`precedent_transactions` on value per key and EV / EBITDA). Differences are reconciled and explained, not averaged away.

### SOP 05. Residual land value and development DCF (owner: Development agent)

Tools: `residual_land_value`, `development_cash_flow`, `residential_absorption`.

1. **Preliminary RLV.** Completed development value less development costs less financing costs less required developer profit, with the completed value deferred to today for development timing and stabilisation.
2. **Discounted RLV for phased developments.** Build the dated project cash flow: acquisition, infrastructure, construction, soft costs, contingency, pre-opening, working capital, taxes, financing and disposal, with operating NOI from FIXVAR and residential receipts from `residential_absorption`. The tool returns the land payment that delivers the required project return, alongside unlevered IRR and NPV, equity IRR and multiple, peak equity and debt, payback and profit on cost.
3. **Rule.** Do not treat a stabilised completed-property value as present-day land value without accounting for development timing, stabilisation and risk. Test the maximum supportable land price against the required project return and report headroom against the asking price.

### SOP 06. Asset-specific underwriting

Apply the drivers in table A4. Underwrite mixed-use components individually, then consolidate into the development cash flow as separate income and cost lines.

### SOP 06a. Debt and equity underwriting (owner: Debt Advisory agent, Chief Investment Officer agent)

1. Debt: the sizing tests in SOP 04 for the stabilised asset; construction loan-to-cost, rate, fees and the capitalisation of interest until opening in `development_cash_flow`; covenants tested through ramp-up.
2. Equity: `equity_waterfall` with the tiers exactly as the shareholders' or JV agreement drafts them (preferred return hurdles, catch-up, promote splits, LP and GP co-invest shares). Report LP and GP IRR and multiples, total promote and its share of profit, and the capital IRR before promote.
3. Acquisition cases: `lbo_returns` and `max_entry_multiple_for_target_irr` for a stabilised asset.
4. Scenarios (M12): downside, base and upside through the whole chain, with `dcf_sensitivity` on the two assumptions that matter most and `build_football_field` to summarise.

### SOP 07. Institutional Investment Memorandum (owner: Capital Markets agent)

The IM must be consistent with the approved model version and identify the valuation date, model version, assumption date and verification status. Sections 1 to 4: executive summary, highlights, transaction, sponsor. Sections 5 to 8: location, market, RNAADR, penetration. Sections 9 to 12: masterplan, components, CAPEX, FIXVAR. Sections 13 to 16: HMEV, RLV, financing, equity waterfall. Sections 17 to 20: returns, sensitivity, risks, exit. Sections 21 to 23: legal and regulatory, investment proposal, appendices.

Report total investment, equity and debt requirements, stabilised revenue, EBITDA, NOI, unlevered IRR, levered IRR, equity multiple, payback, exit value and net proceeds. Separate historical facts, verified data, management assumptions and projections. The agent drafts every section from the approved model and the registers, marks each number with its evidence grade, and leaves the sponsor description, legal opinions and the investment recommendation for human authorship and approval.

### SOP 08. Investor teaser and outreach (owner: Investor Relations agent)

1. Teaser of one to three pages: (1) opportunity and location, (2) development concept and financial KPIs, (3) transaction structure and next steps.
2. Outreach tailored to investor mandate, ticket size, jurisdiction, preferred return and waterfall where relevant; offer NDA and controlled data-room access.
3. Projected returns are never presented as guaranteed. Securities placement, introductions and transaction-linked remuneration may be regulated; jurisdiction-specific legal review precedes external circulation or capital raising. The agent drafts; a human sends.

### SOP 09. Independent validation and quality assurance (owner: Chief Risk Officer agent)

Run every control in table A5 on the current model version. Material D-grade assumptions block unconditional approval. Maintain the source register, assumptions log, version history and the independent reviewer's sign-off. The validation output is a list of failed controls and open assumptions, not a rewritten model.

### SOP 10. AI operating responsibilities

The agent performs the roles in table A6 and names the role it is acting as. Human approval is required for final investment recommendations, legal opinions, regulatory determinations, contractual commitments and external distribution.

### SOP 11. Training and educational scaffolding (owner: Training agent)

Every feasibility engagement yields an annotated training model. Each tool call is annotated with what it computes, the formula, the source of each input and the common error it guards against. Trainees must be able to explain competitive weights, natural vacancy, unaccommodated demand, induced demand, FIXVAR cost drivers, debt constraints, equity yields, cap rates and sensitivity results. Each case includes worked examples, a documented assumption rationale and an assessment exercise. Recommended first cases: a coastal resort with branded residences (the full RNAADR to waterfall chain), an urban hotel (commercial and meeting demand), a heritage conversion (cost and constraint driven), paired with a pari passu JV, a preferred equity with promote over an 8 percent hurdle, and a land-for-equity contribution.

---

## First 30 days: implementation roadmap and the agent's part

| Week | Workstream | Deliverable | Agent contribution |
|---|---|---|---|
| 1 | Audit reference workbooks | Template inventory and model QA | Map the Advanced Concepts, RNAADR, FIXVAR and HMEV workbooks sheet by sheet to tool inputs; reproduce their outputs; log differences |
| 2 | Build connected model | RNAADR to FIXVAR to HMEV / DCF | Run the chain end to end on a reference project; reconcile to the workbooks |
| 3 | Prepare investor documents | IM, teaser and risk templates | Section templates populated from tool outputs with evidence grades |
| 4 | Pilot Is Prendas | Feasibility, model and committee review | Full chain, validation controls, committee memorandum draft |

## Mandatory project deliverables (SOP 15) and where they come from

| Deliverable | Source |
|---|---|
| Project screening and source register; market feasibility and RNAADR demand model | SOP 01; `hotel_market_study` |
| FIXVAR ten-year operating model; HMEV and unlevered DCF; CAPEX and RLV appraisal | `hotel_fixvar_proforma`; `hotel_mortgage_equity_valuation`, `dcf_valuation`; `residual_land_value`, `development_cash_flow` |
| Debt underwriting; equity waterfall; investor returns dashboard; downside sensitivities | Sizing tests, `development_cash_flow`; `equity_waterfall`; headline metrics table; `dcf_sensitivity` and scenario re-runs |
| Independent risk review and investment committee memorandum | Validation controls (A5); committee memorandum draft, decision human |
| Approved institutional IM, one-to-three-page teaser, investor list, proposal correspondence and data-room checklist | SOP 07 and 08 drafts, human approval before distribution |

Operating principle: one project database, one approved model version, traceable assumptions, independent review and human-controlled investor communications.

---

## Appendix 1. Assumptions log template

| ID | Assumption | Value | Unit | Source | Grade (A to D) | Rationale | Owner | Sensitivity tested |
|---|---|---|---|---|---|---|---|---|
| R-01 | Competitive weights by competitor | | x | | | | | |
| R-02 | Stabilised penetration index by segment | | x fair share | | | | | |
| R-03 | Unaccommodated and induced demand by segment | | room nights or percent | | | | | |
| R-04 | ADR index by segment | | x market | | | | | |
| R-05 | Branded residence price and absorption | | EUR per sqm; units per year | | | | | |
| O-01 | Fixed share and driver by expense line | | percent | | | | | |
| O-02 | Replacement reserve | | percent of revenue | | | | | |
| C-01 | Hard, site and soft costs | | EUR | | | | | |
| C-02 | Contingency | | percent | | | | | |
| F-01 | Mortgage rate, amortisation, LTV, DSCR, debt yield | | | | | | | |
| F-02 | Equity yield rate | | percent | | | | | |
| F-03 | Terminal capitalisation rate | | percent | | | | | |
| F-04 | Construction LTC, rate, fees | | | | | | | |
| F-05 | Waterfall tiers | | | | | | | |

## Appendix 2. Headline metrics table template (IM, teaser and returns dashboard)

| Metric | Downside | Base | Upside |
|---|---|---|---|
| Total investment (land, development, finance) | | | |
| Equity requirement and peak equity; debt requirement | | | |
| Stabilised revenue, EBITDA and NOI | | | |
| HMEV value, loan and equity; value per key | | | |
| Unlevered project IRR and NPV at hurdle | | | |
| Levered equity IRR, equity multiple, payback | | | |
| LP IRR and multiple; GP promote | | | |
| Exit value and net sale proceeds | | | |
| Residual land value versus asking price | | | |
| Evidence grade of the material assumptions | | | |

## Appendix 3. Glossary

ADR average daily rate; RevPAR revenue per available room; HARC historic average room count; RNAADR room-night analysis and ADR forecast (working label); FIXVAR fixed and variable component forecast (working label); HMEV hotel mortgage-equity valuation (working label); USALI Uniform System of Accounts for the Lodging Industry; GOP gross operating profit; NOI net operating income; DSCR debt service coverage ratio; LTV loan to value; LTC loan to cost; RLV residual land value; FCFE free cash flow to equity; IM investment memorandum; NDA non-disclosure agreement.

---

*Analytical support for VT Capital Asset Management's internal decision-making under Institutional SOP v2.0. Not investment advice, a valuation report under the RICS Red Book, or a fairness opinion. Human approval is required before any external use.*
