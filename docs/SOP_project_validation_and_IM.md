# Memorandum: Agent Standard Operating Procedure for Project Validation and Investment Memorandum Preparation

**To:** VT Capital Asset Management, Investment Team
**From:** VT Capital Valuation Agent (operating procedure)
**Date:** 20 October 2026
**Subject:** Reference tables and the end-to-end process the agent follows to validate project targets and prepare investment memoranda

This memorandum has two parts. Part A is the reference base: the standards, data sources, formulas, benchmark ranges and tools the agent relies on. Part B is the procedure itself, phase by phase, with the validation gates that have to be passed before a number reaches an investor document. It extends the house process already encoded in the agent (WACC from components, DCF both ways, triangulation, sensitivities, football field) to development and hospitality assets valued by the residual land value method.

Every benchmark range in this document is an indicative starting point for the assumptions log, not a sourced fact for a specific project. The agent must replace each one with a project-specific figure and a citation before it is used in a deliverable.

---

## Part A. Reference tables

### A1. Standards and methodological references

| Area | Reference | How the agent uses it |
|---|---|---|
| Valuation standards | RICS Valuation Global Standards ("Red Book", current edition); International Valuation Standards (IVSC, current edition) | Bases of value (market value, investment value), reporting content, assumptions and special assumptions, hierarchy of inputs |
| Development valuation | RICS professional standard "Valuation of development property" (2019, effective 2020) | Residual method structure, requirement to run both a static residual and a cash-flow residual, risk and sensitivity disclosure |
| Hotel accounting | Uniform System of Accounts for the Lodging Industry (USALI, HFTP and AHLA, current edition) | Departmental revenue and expense structure, GOP, management fees, fixed charges, FF&E reserve, NOI definitions |
| Hotel valuation | HVS hotel valuation methodology; Appraisal Institute hospitality guidance | Income capitalisation of stabilised NOI, discounted cash flow with ramp-up, value per key cross-checks |
| Cost of capital | CAPM; Damodaran country risk and equity risk premium datasets; Kroll (Duff and Phelps) size premium studies; sovereign yields from the ECB and national treasuries | Inputs to the agent's `compute_wacc` and `lever_beta` tools; regional risk premia for Mediterranean jurisdictions |
| Private equity real estate reporting | INREV Guidelines; ILPA Principles; Invest Europe Handbook | Definitions of IRR, equity multiple, DPI, fee and carried-interest disclosure, waterfall reporting |
| Sustainability and regulation | EU Taxonomy, EU Energy Performance of Buildings Directive, BREEAM and LEED, GRESB | ESG section of the IM, capex implications, financing eligibility (green loans) |
| Planning and coastal law | National and regional zoning, coastal protection regimes (e.g. Spain's Ley de Costas, Italian landscape and cultural heritage codes, Greek spatial planning frameworks), local master plans | Buildability, setbacks, height and density limits; always confirmed by local counsel, never assumed |
| Investor communications | Local securities marketing rules (AIFMD marketing provisions, national regulator guidance), firm compliance manual | Forward-looking statement language, disclaimers, NDA and selective disclosure discipline |

### A2. Data sources by workstream

| Workstream | Primary sources | Secondary sources | Agent treatment |
|---|---|---|---|
| Hotel performance benchmarks | STR (CoStar) comp-set reports: occupancy, ADR, RevPAR, supply and demand; HotStats P&L benchmarks | HVS, CBRE Hotels, Horwath HTL, Cushman and Wakefield hospitality research, operator fact sheets | Comp set defined by positioning, not geography alone; trailing 12 months and 5-year history; seasonality by month |
| Residential pricing and absorption | Notarial and cadastral transaction records; developer price lists; sold-out timelines of comparable schemes | Knight Frank Wealth Report and prime indices, Savills branded residences research, Idealista and similar portals, Eurostat and ECB house price indices | Asking prices discounted to achieved prices; branded premium evidenced by paired comparables, not assumed |
| Tourism demand | National statistics offices (INE, ISTAT, ELSTAT, INE Portugal), UN Tourism barometer, airport authority traffic statistics, Eurocontrol | Airline schedule data, cruise and marina operator statistics, destination marketing organisations | Feeder-market split, seasonality, length of stay, growth versus supply pipeline |
| Construction costs | Local quantity surveyor cost plans; tender returns on comparable projects | RICS BCIS, Turner and Townsend International Construction Market Survey, Arcadis International Construction Costs | Cost per sqm GFA and per key by specification tier; escalation to midpoint of construction |
| Yields and transaction evidence | Hotel and residential transaction databases (MSCI Real Capital Analytics, agent deal lists), broker investment outlooks (CBRE, JLL, Savills, Cushman and Wakefield) | HVS European Hotel Valuation Index, published deal announcements | Exit yields by market, brand tier and vintage; value per key; precedent EV to EBITDA via the agent's `precedent_transactions` tool |
| Macro and rates | ECB, IMF World Economic Outlook, OECD, national central banks | Bank lending surveys, sovereign spreads | Risk-free rate, inflation for cost and ADR escalation, debt pricing |
| Site and legal | Title deeds, cadastral plans, topographical and geotechnical surveys, environmental impact assessments, planning certificates | Satellite imagery, drive-time analysis, infrastructure plans | Buildable area, constraints register, permitting timeline and risk |

### A3. Key performance indicators and formulas

| KPI | Formula | Notes and sanity checks |
|---|---|---|
| Occupancy | Rooms sold / rooms available | Stabilised occupancy should not exceed the comp set's stabilised level without a documented demand gap |
| ADR | Rooms revenue / rooms sold | Premium to comp set must be justified by product, brand and scarcity |
| RevPAR | Occupancy x ADR | Primary top-line driver; compare index to comp set (RevPAR index) |
| TRevPAR | Total hotel revenue / rooms available | Captures F&B, spa, beach club and other ancillary revenue |
| GOP and GOP margin | Total revenue less departmental and undistributed expenses; GOP / total revenue | Luxury resorts typically 30 to 40 percent; above 45 percent needs explanation |
| GOPPAR | GOP / rooms available | Profit benchmark per key |
| Management fees | Base fee (percentage of total revenue) plus incentive fee (percentage of GOP or adjusted GOP) | Indicative: base 2 to 3 percent, incentive 8 to 10 percent; confirm against the HMA term sheet |
| FF&E reserve | Percentage of total revenue set aside for renewals | Indicative 3 to 5 percent, stepping up over the first years of operation |
| NOI (hotel EBITDA after reserve) | GOP less management fees, fixed charges and FF&E reserve | The figure capitalised at exit; the IM's "stabilised EBITDA" must state whether it is before or after the reserve |
| Gross development value (GDV) | Hotel exit value (stabilised NOI / exit yield) plus net residential sales plus ancillary asset values | Residential sales net of selling costs, brand licence fees and VAT where applicable |
| Total development cost (TDC) | Land plus hard costs plus site infrastructure plus soft costs plus FF&E and OS&E plus pre-opening plus contingency plus finance costs | Stated with and without land, and with and without finance, so that the residual can be read directly |
| Residual land value (RLV) | GDV less TDC excluding land less finance costs less required developer profit | The maximum justifiable land price; compare to the asking price and the vendor's expectations |
| Profit on cost | (GDV less TDC) / TDC | Indicative requirement 15 to 20 percent for resort development, higher where planning risk is retained |
| Profit on GDV | (GDV less TDC) / GDV | Alternative presentation used by some lenders |
| Yield on cost | Stabilised NOI / TDC (hotel component) | Should exceed the exit yield by a development margin, typically 150 to 300 basis points |
| Exit yield (cap rate) | Stabilised NOI / exit value | Benchmarked to transaction evidence by market and brand tier |
| Value per key | Hotel value / number of keys | Cross-check against transactions; the old rule of thumb (roughly 1,000 x ADR) is a coarse sanity check only |
| Cost per key | Hotel TDC / number of keys | Compare to value per key; a cost per key above value per key fails the residual |
| Absorption rate | Units sold per month (or per quarter) | Must be at or below the achieved pace of comparable schemes; branded product may sell faster but not without evidence |
| Sell-out period | Units / absorption rate | Drives the cash-flow residual; test with a 6 and 12 month slip |
| Unlevered project IRR | Rate at which the NPV of development and operating cash flows (before debt) is zero | Compared to the project WACC and to the target return for the risk stage |
| Levered (equity) IRR | IRR of equity contributions and distributions after debt service | Reported alongside the equity multiple; leverage increases dispersion, not only returns |
| Equity multiple (MOIC) | Total distributions / total equity contributed | Report with the hold period; a 2.0x over 8 years is a very different deal from 2.0x over 4 |
| Payback period | First year in which cumulative distributions equal contributed equity | State whether undiscounted or discounted |
| DSCR | Cash flow available for debt service / debt service | Covenant typically 1.20x to 1.35x for stabilised hotels; interest cover during ramp-up tested separately |
| LTC and LTV | Loan / total cost; loan / value | Indicative development LTC 50 to 60 percent; confirm with lender soundings |
| FCFE | NOI less capex less interest less principal plus net new borrowing | The basis for the equity waterfall and for the FCFE projection in the model |
| Waterfall tiers | Return of capital, preferred return, catch-up, carried interest split | Documented per the shareholders' or LP agreement; the agent models tiers exactly as drafted, never from memory |
| Break-even occupancy | Occupancy at which NOI covers debt service (or fixed costs) | Headline downside statistic for the IM risk section |

### A4. Indicative benchmark ranges for the assumptions log

These are starting points for a Mediterranean luxury resort with branded residences. Each must be replaced with a project-specific, sourced figure before use.

| Assumption | Indicative range | Replace with |
|---|---|---|
| Hotel ramp-up to stabilisation | 3 to 4 operating years; e.g. year 1 at 75 percent of stabilised RevPAR, year 2 at 90 percent | Operator's underwriting, comp-set openings history |
| Stabilised occupancy, seasonal luxury resort | 55 to 70 percent annual (with peak months above 90 percent) | STR comp set, seasonality calendar |
| ADR premium for new branded luxury supply | 10 to 30 percent over the existing comp set | Paired comparables, operator pipeline data |
| Branded residence price premium | 20 to 35 percent over comparable unbranded product in the same location | Paired transactions, Savills and Knight Frank branded residences research |
| Brand licence or marketing fee on residential sales | 3 to 5 percent of gross sales | Residential licence agreement term sheet |
| Soft costs | 12 to 20 percent of hard costs | Consultant fee proposals, permit tariffs |
| Contingency | 5 to 10 percent of hard costs, higher pre-tender | Quantity surveyor's risk register |
| FF&E and OS&E | Per key, by brand tier; confirm against the brand's technical services standards | Operator's technical services budget |
| Pre-opening and working capital | Several months of operating expenses plus sales and marketing | Operator's pre-opening budget |
| Developer profit requirement | 15 to 20 percent on cost | Investment committee return policy |
| Exit yield, luxury resort hotel, prime Mediterranean | Benchmark to current transaction evidence; test plus and minus 50 basis points | Broker investment outlooks, MSCI, deal announcements |
| Discount rate, development stage | Project WACC plus a development risk premium that falls as planning, procurement and pre-sales de-risk the project | `compute_wacc` plus a documented stage premium |

### A5. Agent tool coverage

| Process step | Agent tool | Status |
|---|---|---|
| Cost of equity, WACC, beta levering | `compute_wacc`, `lever_beta` | Available |
| Operating cash-flow projection from growth, margin and reinvestment assumptions | `project_free_cash_flows` | Available (corporate form; used for the stabilised hotel operating company) |
| Discounting, terminal value, enterprise to equity bridge | `dcf_valuation` | Available |
| Two-way sensitivity tables | `dcf_sensitivity` | Available |
| Trading comparables (listed hotel and resort owners, developers) | `trading_comps` | Available |
| Precedent transactions (asset and portfolio deals, value per key cross-check through EV / EBITDA) | `precedent_transactions` | Available |
| Sponsor returns, ability to pay at a target IRR | `lbo_returns`, `max_entry_multiple_for_target_irr` | Available |
| Range synthesis | `build_football_field` | Available |
| NPV, IRR and CAGR on arbitrary series (construction draws, waterfall flows) | `financial_calculator` | Available |
| Hotel pro forma under USALI (occupancy and ADR ramp to NOI) | `hotel_proforma` | Planned |
| Residential sales schedule (unit mix, pricing, absorption, deposits) | `residential_absorption` | Planned |
| Development cash flow (S-curve draws, capitalised interest, funding sequence) and FCFE | `development_cash_flow` | Planned |
| Static and cash-flow residual land value | `residual_land_value` | Planned |
| Equity waterfall | `equity_waterfall` | Planned |
| Mapping of the "Advanced Concepts - complete.xls" template | Sheet-by-sheet mapping of inputs to tool parameters | Pending receipt of the template |

Until the planned tools ship, the agent builds the hotel pro forma, residential schedule and residual explicitly in the conversation using `financial_calculator` for every discounting step, shows each intermediate figure, and labels the result as a manual build subject to model review.

---

## Part B. Memorandum: the agent's procedure

### Phase 0. Intake, mandate and data inventory

1. **Define the mandate.** Asset class (coastal resort, urban mixed-use, repositioning), development stage (land option, permitted, under construction, operating), deliverable requested (feasibility note, full IM, teaser, trainee case study) and the decision it supports (land bid, equity raise, JV negotiation).
2. **Fix conventions.** Currency and unit (EUR thousands or millions), measurement basis (gross floor area, net saleable area, keys), valuation date, price basis (nominal with explicit inflation, or real), and fiscal treatment (VAT, transfer tax, corporate tax rate).
3. **Inventory the data room.** List every document received, its date and author. Grade each input A to D: A sourced and current, B sourced but dated or indirect, C sponsor estimate, D agent assumption. Nothing graded C or D reaches an investor document without being flagged as such.
4. **Open the assumptions register.** One row per assumption: value, unit, source, grade, rationale, owner, sensitivity tested (yes or no). The register is the audit trail and the trainee annotation layer at the same time.
5. **Ask before assuming** when a missing input is central (land price, key count, unit mix, operator terms, exit yield). Proceed with a labelled assumption only when the question is peripheral or the user has asked for a first cut.

### Phase 1. Market research and target validation

1. **Site and location.** Record drive times to the nearest international airports and their seat capacity and seasonality, access roads, proximity to demand generators (marinas, beaches, golf, cultural sites, conference venues), topography and views, utilities, and the constraints register (coastal setbacks, protected habitat, heritage, height and density caps). Flag any item that depends on an unobtained permit.
2. **Demand profiling.** Split demand into leisure versus MICE and domestic versus international feeder markets. For each feeder market record arrivals growth, average length of stay, spend per visitor and airline connectivity. State the share of demand the project needs to capture at stabilisation and compare it to the comp set's capture.
3. **Competitive set.** Define the comp set by positioning (brand tier, product type, price point) first and geography second. For hotels: trailing 12-month occupancy, ADR, RevPAR, seasonality and new supply pipeline with opening dates. For residential: achieved price per sqm, absorption, unit mix, premium for sea view and branded product, unsold inventory.
4. **Gap analysis.** State explicitly which gap the project fills (no branded luxury product, no master-planned estate with amenities, no marina-linked residences) and what evidence supports it. A gap claim without pricing evidence is a hypothesis, not a validated assumption.
5. **Validation tests.** Each revenue assumption must pass at least one of these before it enters the model:
   - Stabilised occupancy at or below the comp set's stabilised level, unless a documented demand gap justifies a premium.
   - ADR premium to the comp set explained by product, brand and scarcity, and within the range of premia achieved by comparable new openings.
   - Residential price per sqm within the top quartile of achieved (not asking) comparables; any branded premium evidenced by paired comparables.
   - Absorption at or below the achieved pace of the fastest comparable scheme.
   - Projected RevPAR index versus the comp set below 130 unless the product is demonstrably a tier above.

### Phase 2. Revenue build

1. **Hotel.** Keys x available nights x occupancy x ADR gives rooms revenue by year, with a three to four year ramp. Add F&B, spa and wellness, beach club, retail, rentals and other operated departments as a percentage of rooms revenue or per occupied room, benchmarked to the comp set's TRevPAR. Apply USALI departmental expenses, undistributed expenses, management fees, fixed charges (property tax, insurance) and the FF&E reserve to reach NOI. Report GOP margin, GOPPAR and NOI per key.
2. **Residential.** Unit schedule with type, count, net saleable area, price per sqm and total price. Sales timeline from launch through sell-out at the validated absorption rate, with the deposit and completion payment structure, selling costs, brand licence fees and VAT. Distinguish premium (unbranded) and branded villas with their own pricing and absorption curves, as in the example of premium villas at EUR 6,300 per sqm and branded villas at EUR 7,400 per sqm.
3. **Ancillary and rental pool.** Marina berths, golf memberships, rental programme income shared with owners, ground leases. Each has its own source and its own sensitivity.
4. **Escalation.** State inflation applied to ADR, costs and prices separately. Real growth above inflation requires a written justification.

### Phase 3. Cost build

1. **Hard costs** per sqm of gross floor area by building type (hotel, villas, amenities, back of house), with the quantity surveyor's cost plan as the source and escalation to the midpoint of construction.
2. **Site infrastructure** (earthworks, roads, utilities, landscaping, coastal works) separated from building costs because it is incurred early and is often underestimated.
3. **Soft costs**: design and engineering, permits and fees, project management, legal, marketing and sales commissions, operator technical services, pre-opening, insurance.
4. **FF&E and OS&E** per key and per residence to the brand standard.
5. **Contingency** on hard and soft costs, sized to the design stage.
6. **Finance costs**: arrangement fees and interest on the drawn balance through construction and ramp-up, with interest capitalised until the hotel covers it. Finance costs are shown separately so that the unlevered residual can be read.
7. **Land**: asking price, transaction costs and holding costs, carried as a separate line so that the residual can be solved for it.

### Phase 4. Residual land value

1. **Static residual.** GDV (hotel stabilised NOI divided by the exit yield, plus net residential sales, plus ancillary values) less TDC excluding land, less finance costs, less the required developer profit on cost, equals the RLV. Present the calculation as a one-page bridge from GDV to RLV.
2. **Cash-flow residual.** Build the full development and operating cash flow (draws on an S-curve, residential receipts by milestone, hotel ramp-up, exit at stabilisation plus one or two years) and solve for the land value that delivers the target unlevered IRR. Use `financial_calculator` (NPV at the target rate) or, when the planned `residual_land_value` tool is available, that tool directly.
3. **Reconcile the two.** Differences between the static and cash-flow residuals come from timing (long sell-out, slow ramp) and must be explained in the memorandum.
4. **Decision test.** Compare the RLV to the asking land price. If the asking price exceeds the RLV, state the ADR, price per sqm or cost reduction that would be needed to close the gap and whether the market evidence supports it. Do not solve the gap by raising assumptions without new evidence.

### Phase 5. Financial modelling and returns

1. **Discount rate.** Build the WACC with `compute_wacc` from the sovereign risk-free rate, a relevered beta for hotel and resort real estate owners (`lever_beta` from listed peers), the equity risk premium, a country risk premium where relevant, the project's debt pricing and target leverage. Add a documented development-stage premium that steps down at permitting, procurement and pre-sales milestones.
2. **Unlevered DCF.** Value the stabilised hotel with `dcf_valuation` using both the perpetuity method and an exit-yield-based terminal value, and read the implied exit multiple and implied growth cross-checks. Run `dcf_sensitivity` on discount rate against exit yield (or growth).
3. **Funding and FCFE.** Sequence equity first, then debt draws to the agreed LTC; capitalise interest in construction; apply the cash sweep or amortisation profile; compute FCFE by year and the equity waterfall per the agreement. Use `lbo_returns` for a stabilised-asset acquisition case and `financial_calculator` for the construction-period flows until the planned development tools ship.
4. **Headline metrics.** Total investment (with and without land and finance), unlevered IRR, levered IRR, equity multiple, payback period, stabilised EBITDA or NOI (stating the reserve treatment), yield on cost, profit on cost, peak equity, peak debt, DSCR at stabilisation and break-even occupancy.
5. **Sensitivities and scenarios.** At minimum: ADR plus and minus 10 percent; occupancy plus and minus 5 points; hard costs plus and minus 10 percent; exit yield plus and minus 50 basis points; construction delay of 6 and 12 months; absorption slowed by 25 percent; residential price plus and minus 10 percent. Present base, downside and upside cases with the probability-weighted view the investment committee prefers.
6. **Relative value.** Cross-check the stabilised hotel value per key and EV to EBITDA against `precedent_transactions`, and listed-owner multiples against `trading_comps`; summarise all ranges with `build_football_field`.

### Phase 6. Sanity checks and validation gates

The agent does not release a figure to an IM draft until each gate is passed or the exception is documented in the assumptions register.

| Gate | Test | Action on failure |
|---|---|---|
| Terminal weight | Present value of exit below 75 percent of hotel value | Extend the explicit period or explain the exit dependence prominently |
| Implied metrics | Implied exit multiple and implied growth within comp evidence | Revisit the exit yield or growth assumption |
| Yield on cost spread | Yield on cost exceeds exit yield by the required development margin | The scheme does not create value; revisit cost, pricing or land |
| Cost versus value per key | Cost per key below value per key | Residual fails; report rather than adjust |
| Absorption realism | Sell-out period within observed comparables | Slow the schedule and re-run the cash-flow residual |
| Leverage | DSCR and LTC inside lender terms through ramp-up | Resize debt or add equity; report the effect on IRR |
| Internal consistency | Keys, areas and unit counts identical across site plan, cost plan and revenue model; totals reconcile to the sum of lines | Fix the source table; never hard-code a reconciling item |
| Warnings | All warnings returned by the tools reviewed and either resolved or restated to the user | Material warnings appear in the IM risk section |

### Phase 7. Investment memorandum assembly

The IM is written in an institutional, data-driven register. Every number in the IM traces to the assumptions register and to a tool output or source document. Section order and minimum content:

1. **Executive summary.** Transaction overview, deal structure (SPV, JV, equity and debt split), capital requested, use of proceeds, headline returns (total investment, IRR, equity multiple, payback, stabilised EBITDA), timeline and the three reasons the opportunity exists.
2. **Investment thesis.** The market gap, the scarcity argument, the brand or operator partnership, the sponsor's track record and the de-risking milestones already achieved.
3. **Site and masterplan.** Location, access and drive times, topography and views, zoning and permitted parameters, constraints, and the asset breakdown: hotel keys by category, branded versus premium residences by type and area, amenities (spa, beach club, marina, golf, F&B), phasing.
4. **Market analysis.** Demand profile, feeder markets, comp set tables for hotel and residential, supply pipeline, pricing evidence and the validation tests passed in Phase 1.
5. **Business plan.** Hotel pro forma (occupancy, ADR, RevPAR, TRevPAR, GOP, NOI by year), residential sales schedule and pricing, operator and brand terms, operating structure.
6. **Development plan and budget.** Capital expenditure by category, cost per sqm and per key benchmarks, programme with milestones, procurement strategy, permitting status and risks, contingency policy.
7. **Financial projections.** Sources and uses, funding timeline, unlevered and levered cash flows, FCFE, waterfall, headline metrics table, sensitivity tables and scenarios, football field.
8. **Exit strategy.** Hold period, exit route (single-asset sale to an institutional hotel investor, sale with residences sold out, refinancing and hold), exit yield assumption with transaction evidence, and the reversionary value bridge.
9. **Risk factors and mitigants.** Planning, construction, cost inflation, market, operator, financing, FX and regulatory risks, each with mitigant and the sensitivity result that quantifies it.
10. **Structure, governance and terms.** Vehicle, governance rights, fees, waterfall, reporting, key-person and exit provisions.
11. **Appendices.** Assumptions register, comp set detail, cost plan summary, model outputs, team biographies, legal and technical due diligence summaries, disclaimer.

The agent drafts sections 1, 4, 5, 7, 8 and 9 in full from the model and the register, drafts 3 and 6 from the data room with gaps flagged, and leaves 2, 10 and the biographies for the deal team, offering structure and prompts.

### Phase 8. Investor teaser and outreach

1. **Teaser (maximum three pages).** Page 1: location, concept and the single image that explains the site; page 2: masterplan summary and unique selling propositions; page 3: KPI table (total capex, equity requirement, IRR, equity multiple, stabilised EBITDA, timeline) and the ask. No assumption appears in the teaser that is not in the IM.
2. **Proposal email.** Tailored to the recipient's mandate (core-plus hotel investor, family office, operator-investor, development lender). Four parts: why this partner, what is being offered (JV or equity ticket, governance), targeted returns with the risk framing, and a specific call to action (site visit dates or NDA execution). Length under 250 words.
3. **Compliance.** Forward-looking statements carry the firm's disclaimer; returns are "targeted", never "expected" or "guaranteed"; confidential material goes out only after NDA; the agent checks the draft against the compliance manual before release and flags anything it cannot verify.

### Phase 9. Trainee mentorship and educational scaffolding

1. **Model annotations.** Every model section carries a short note: what the block computes, the formula, the source of each input and the common error it guards against (for example, discounting the exit at the wrong period, double counting the FF&E reserve, mixing gross and net areas).
2. **Assumption justifications.** The assumptions register's rationale column is written for a junior reader: why scarcity supports the ADR premium, why the discount rate carries a country premium, why the contingency is sized as it is.
3. **Methodology primers.** One page each on the residual method (static and cash flow), DCF versus income capitalisation, FCFE and the equity waterfall, and the difference between project and equity IRR.
4. **Case studies.** Each closed or declined project becomes an anonymised case: brief, data pack, model, memorandum extract, the committee's decision and the lessons. Recommended order for the first set: (i) a coastal resort with branded residences, since it is the firm's core product and exercises the full residual method; (ii) an urban mixed-use repositioning, which introduces existing-income analysis, vacancy and refurbishment phasing; (iii) a marina-led master plan, which adds infrastructure phasing and ancillary income streams.
5. **Review loop.** Trainee drafts are reviewed against the Phase 6 gates; the agent produces a marked-up list of failed gates and open assumptions rather than a rewritten model.

### Phase 10. Quality control, versioning and audit trail

1. **Versioning.** Each model and document version is dated and numbered; the change log records what moved and why. Returns are never quoted without the version.
2. **Integrity checks.** Sources equal uses; balance of funding each period; areas and counts reconcile across sections; no hard-coded reconciling items; sensitivity base case equals the headline case.
3. **Sign-off matrix.** Analyst builds, associate reviews the model, principal reviews the memorandum, compliance reviews external documents.
4. **Retention.** The assumptions register, tool outputs and source documents are stored with the deliverable so that any number can be reproduced.

---

## Appendix 1. Assumptions register template

| ID | Assumption | Value | Unit | Source | Grade (A to D) | Rationale | Owner | Sensitivity tested |
|---|---|---|---|---|---|---|---|---|
| R-01 | Stabilised occupancy | | percent | | | | | |
| R-02 | Stabilised ADR | | EUR | | | | | |
| R-03 | Branded villa price | | EUR per sqm | | | | | |
| C-01 | Hard cost, hotel | | EUR per sqm GFA | | | | | |
| C-02 | Contingency | | percent of hard cost | | | | | |
| F-01 | Exit yield | | percent | | | | | |
| F-02 | Discount rate | | percent | | | | | |
| F-03 | LTC | | percent | | | | | |

## Appendix 2. Headline metrics table template (IM and teaser)

| Metric | Base case | Downside | Upside |
|---|---|---|---|
| Total investment (incl. land and finance) | | | |
| Equity requirement and peak equity | | | |
| Unlevered project IRR | | | |
| Levered equity IRR | | | |
| Equity multiple | | | |
| Payback period | | | |
| Stabilised EBITDA / NOI (after FF&E reserve) | | | |
| Yield on cost | | | |
| Profit on cost | | | |
| Exit yield and exit value | | | |
| Residual land value versus asking price | | | |

## Appendix 3. Glossary

ADR average daily rate; RevPAR revenue per available room; TRevPAR total revenue per available room; GOP gross operating profit; NOI net operating income; FF&E furniture, fixtures and equipment; OS&E operating supplies and equipment; GDV gross development value; TDC total development cost; RLV residual land value; LTC loan to cost; LTV loan to value; DSCR debt service coverage ratio; FCFE free cash flow to equity; MOIC multiple on invested capital; HMA hotel management agreement; MICE meetings, incentives, conferences and exhibitions; USALI Uniform System of Accounts for the Lodging Industry.

---

*Analytical support for VT Capital Asset Management's internal decision-making. Not investment advice, a valuation report under the RICS Red Book, or a fairness opinion.*
