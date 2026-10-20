# Memorandum: Agent Standard Operating Procedure for Project Validation and Investment Memorandum Preparation

**To:** VT Capital Asset Management, Investment Team
**From:** VT Capital Valuation Agent (operating procedure)
**Date:** 20 October 2026
**Subject:** Reference tables and the end-to-end process the agent follows to validate project targets (RNAADR, FIXVAR, HMEV, residual land value) and prepare investor deliverables

This memorandum has two parts. Part A is the reference base: the standards, data sources, formulas, benchmark ranges and tools the agent relies on. Part B is the procedure itself, phase by phase, with the validation gates that have to be passed before a number reaches an investor document. For hotels and resorts the procedure follows the HVS sequence: the built-up approach based on an analysis of lodging activity for market penetration and rate (RNAADR), the fixed and variable component approach for the ten-year forecast of revenue and expense (FIXVAR), the mortgage-equity technique for value (HMEV) and, for greenfield sites, the residual land value. The corporate house process already encoded in the agent (WACC from components, DCF both ways, comps and precedents, sensitivities, football field) remains the cross-check.

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
| Market study (RNAADR) | Rushmore and Baum, *Hotels and Motels: Valuations and Market Studies* (Appraisal Institute); HVS built-up approach based on an analysis of lodging activity | Competitive set definition, competitive weighting, HARC, demand segmentation, unaccommodated and induced demand, fair share, market share and penetration indices, ADR by segment |
| Forecast of revenue and expense (FIXVAR) | HVS fixed and variable component approach; USALI line structure | Base statement at base occupancy and ADR, fixed and variable shares by line, variability indices, inflation to nominal currency, reserve for replacement |
| Mortgage-equity valuation (HMEV) | HVS simultaneous valuation formula; Appraisal Institute mortgage-equity (Ellwood and Akerson) literature | Loan sizing on LTV, debt coverage ratio and debt yield; equity yield rate; ten-year hold; terminal capitalisation; equity residual |
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
| Historic average room count (HARC) | Rooms x share of the base year the hotel was open | Puts a hotel that opened or closed mid-year on a comparable footing |
| Effective rooms | HARC x competitive weight (1.0 primary, lower for secondary) | Basis for fair share |
| Accommodated room nights | HARC x 365 x occupancy x segment share | Summed over the set to give base-year demand by segment |
| Fair share | Hotel effective rooms / market effective rooms | What the hotel would capture if all hotels were equally competitive |
| Market share | Hotel room nights in the segment / segment room nights | Observed capture |
| Penetration (competitive) index | Market share / fair share | Above 1.0 outperforms the set in that segment; the subject's index is projected per segment per year and ramps to stabilisation |
| Unaccommodated demand | Room nights turned away because of capacity constraints, as a share of accommodated demand | Added to market demand when new supply opens; evidenced by peak-period sell-outs |
| Induced demand | Room nights created by a new generator (the subject's facilities, a new convention centre, a marina) | Added per year; must be tied to a named generator |
| Variability index | Projected utilisation / base utilisation in real terms (occupancy, department revenue or total revenue) | Drives the variable component of every FIXVAR line |
| FIXVAR line projection | Base x inflation factor x (fixed share + variable share x variability index) | Rooms expense: fixed 50 to 70 percent on occupancy; undistributed: on total revenue; property tax and insurance: fixed |
| Mortgage constant | Annual debt service / loan, for the amortisation term and payment frequency | Converts the loan into the debt service deducted from NOI |
| Loan sizing tests | LTV x value; NOI year 1 / (DCR x constant); NOI year 1 / debt yield | The most restrictive loan governs the concluded value |
| Simultaneous valuation formula | V = (PV of NOI years 1 to n at the equity yield + net reversion discounted n years) / (1 - M + f M a_n + M P_n d_n) | M = LTV, f = mortgage constant, a_n = annuity factor, P_n = loan balance share after n years, d_n = single discount factor |
| Equity residual | Year n+1 NOI / terminal cap rate, less selling costs, less the loan balance | Discounted at the equity yield and added to the discounted equity cash flows |
| Going-in capitalisation rate | NOI year 1 / value | Reasonableness check against transaction evidence and the terminal rate |

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
| Equity yield rate (HMEV) | Before-tax equity yield reflecting the asset's risk; test a 200 basis point band | Investor surveys, sponsor return policy, recent hotel equity raises |
| Hotel mortgage terms | Interest rate, 20 to 25 year amortisation, LTV 55 to 65 percent, DCR 1.30x to 1.50x, debt yield 9 to 11 percent | Lender soundings for the specific asset and market |
| Terminal capitalisation rate | Going-in rate plus 50 to 100 basis points for a ten-year hold | Transaction evidence, broker outlooks |
| Reserve for replacement | 4 percent of total revenue (HVS convention), lower in opening years | Hotel management agreement |
| Rooms department expense split | 50 to 70 percent fixed, 30 to 50 percent variable with occupancy | Comparable operating statements, HotStats |

### A5. Agent tool coverage

| Process step | Agent tool | Status |
|---|---|---|
| RNAADR market study: competitive set, HARC, base-year demand by segment, fair share, market share, penetration indices, latent and induced demand, new supply, subject occupancy, segment ADR, blended ADR and RevPAR by year | `hotel_market_study` | Available |
| FIXVAR forecast of revenue and expense: base statement, fixed and variable shares, variability indices, inflation, departmental and undistributed expenses, management fees, fixed charges, reserve for replacement, NOI | `hotel_fixvar_proforma` | Available |
| HMEV mortgage-equity valuation: mortgage constant, loan sizing on LTV, DCR and debt yield, equity cash flows, equity residual at the terminal cap rate, simultaneous valuation formula, going-in cap rate, value per key | `hotel_mortgage_equity_valuation` | Available |
| Residual land value for a greenfield project: stabilised value deferred to today less development, financing and developer profit, headroom against the asking price | `residual_land_value` | Available |
| Cost of equity, WACC, beta levering (discount rate for the unlevered DCF cross-check) | `compute_wacc`, `lever_beta` | Available |
| Unlevered DCF cross-check of the mortgage-equity value, with implied exit multiple and implied growth | `dcf_valuation`, `dcf_sensitivity` | Available |
| Operating projection from growth, margin and reinvestment assumptions (non-hotel components) | `project_free_cash_flows` | Available |
| Trading comparables and precedent transactions (value per key, EV to EBITDA) | `trading_comps`, `precedent_transactions` | Available |
| Sponsor returns and ability to pay at a target IRR | `lbo_returns`, `max_entry_multiple_for_target_irr` | Available |
| Range synthesis | `build_football_field` | Available |
| NPV, IRR and CAGR on arbitrary series (construction draws, waterfall flows) | `financial_calculator` | Available |
| Residential sales schedule (unit mix, pricing, absorption, deposits) for mixed-use schemes | Manual build with `financial_calculator` | Planned as a tool |
| Monthly development cash flow with S-curve draws and capitalised interest | Manual build with `financial_calculator`; `residual_land_value` uses an average-drawn approximation | Planned as a tool |
| Equity waterfall (return of capital, preferred return, catch-up, promote) | Manual build with `financial_calculator` | Planned as a tool |
| Mapping of the RNAADR, FIXVAR and HMEV workbooks | Sheet-by-sheet mapping of inputs to tool parameters | Pending receipt of the workbooks |

---|---|---|
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

### Phase 1. Market research and target validation (RNAADR)

Tool: `hotel_market_study`. The agent runs the built-up approach based on an analysis of lodging activity and does not accept an occupancy or ADR assumption that has not come out of it.

1. **Define the market and the competitive set.** Record the primary market area and list primary and secondary competitors with room count, opening date, positioning and amenities. Give each a competitive weight (1.0 for a primary competitor, typically 0.25 to 0.75 for a secondary one) so that effective rooms reflect how directly each hotel competes. Record the share of the base year each was open to compute the historic average room count (HARC).
2. **Segment demand.** Split each competitor's occupancy into the primary market segments (typically Commercial, Meeting and Convention, Leisure; resorts often add Group Leisure or Wholesale). Segment shares must sum to one per hotel and be evidenced by operator data, STR segmentation or interviews.
3. **Determine base-year demand.** Accommodated room nights per segment are the sum over the set of HARC x 365 x occupancy x segment share. The tool returns the base-year table: effective rooms, fair share, room nights, market share and penetration index per segment for every competitor. Check that the competitor indices are consistent with their known positioning before going further.
4. **Quantify latent demand.** Unaccommodated demand is entered per segment as a share of base-year accommodated demand, evidenced by peak-period sell-outs, compression nights and turn-away data. Induced demand is entered per segment per year and tied to a named generator (the subject's conference space or spa, a new marina, an airport route). Latent demand without evidence stays at zero.
5. **Project supply and demand.** Enter segment growth rates (from tourism statistics and airline capacity), new competitive supply with opening year, first-year fraction and penetration indices, and the subject's rooms, opening fraction and penetration index per segment per year. The subject's indices ramp from below 1.0 at opening to the stabilised level that product, brand and amenities justify. The tool normalises market shares across the set in each year (the market share adjuster) and returns the subject's room nights, occupancy, market share and overall penetration by year.
6. **Forecast ADR.** Enter market ADR by segment in base-year currency, the subject's ADR index per segment (its rate positioning against the segment at stabilisation) and an optional ramp for the opening years; the tool inflates and blends them by the subject's segment mix to give ADR, RevPAR and rooms revenue by year.
7. **Validation tests.** The RNAADR output passes only if: stabilised occupancy is consistent with the comp set's stabilised level after new supply; the overall penetration at stabilisation is below 1.3 unless the product is demonstrably a tier above; the ADR index per segment is supported by paired comparables; and every latent-demand entry has a named source. The tool's warnings (occupancy above 80 percent, penetration above 1.3) are resolved or restated to the user.

### Phase 2. Forecast of revenue and expense (FIXVAR)

Tool: `hotel_fixvar_proforma`, fed with the RNAADR occupancy and ADR series.

1. **Establish the base statement.** State the subject's first representative year of operation in current currency at a base occupancy and the base ADR: rooms revenue, each other operated department (F&B, spa and wellness, beach club, retail, other), departmental expenses, undistributed expenses (administrative and general, marketing, property operations and maintenance, utilities), management fees, fixed charges (property tax, insurance) and the reserve for replacement. Sources are comparable operating statements, HotStats benchmarks and the operator's underwriting.
2. **Apply fixed and variable ratios.** Give every line a fixed share and a variability index: rooms expense 50 to 70 percent fixed on occupancy; other departmental expenses on their own department's revenue; undistributed expenses largely fixed with the variable share on total revenue; property tax and insurance fixed; the reserve as a straight percentage of total revenue (4 percent by convention, lower in opening years if the agreement allows).
3. **Project.** The tool inflates each line to nominal currency and projects it as base x inflation x (fixed share + variable share x index ratio), where the index ratio compares the projected year to the base year in real terms. Ten years plus the reversion year are projected for the HMEV.
4. **Read the statement.** Check departmental profit margins, GOP margin (luxury resorts typically 30 to 40 percent), NOI margin and NOI per available room against the comp set. The tool flags GOP margins above 50 percent or below 20 percent and any year of negative NOI, which must be covered by working capital in the budget.
5. **Mixed-use components.** Residential sales, rental pools, marina and ancillary income are built alongside with their own sources and sensitivities (unit schedule, price per sqm, absorption, deposit structure, selling costs, brand licence fees); until the residential tool ships this is a manual build with `financial_calculator` and every intermediate figure shown.

### Phase 3. Cost build

1. **Hard costs** per sqm of gross floor area by building type, from the quantity surveyor's cost plan, escalated to the midpoint of construction.
2. **Site works** (earthworks, roads, utilities, landscaping, coastal works) separated from building costs.
3. **Soft costs**: design and engineering, permits and fees, project management, legal, marketing and sales, operator technical services, insurance.
4. **FF&E and OS&E** per key to the brand standard; **pre-opening and working capital** from the operator's budget.
5. **Contingency** on hard and site costs, sized to the design stage.
6. **Finance**: construction loan to cost, interest rate, period and average drawn balance, plus arrangement fees.
7. **Land**: asking price and transaction costs, carried separately so that the residual can be solved for it.

### Phase 4. Valuation (HMEV)

Tool: `hotel_mortgage_equity_valuation`, fed with the FIXVAR net operating income for the holding period plus one year.

1. **Establish debt underwriting criteria.** From current lender soundings: mortgage interest rate, amortisation period, loan-to-value limit, minimum debt coverage ratio on year-one income and minimum debt yield. All three sizing tests are entered; the tool computes the loan each implies and takes the most restrictive as the loan a lender would advance. The DCR and debt-yield tests are applied to year-one income by default; when the lender sizes on stabilised income, set the sizing year to the first stabilised year and say so in the memorandum.
2. **Determine the equity yield and reversion.** Set the before-tax equity yield rate for the asset's risk (stage, market, brand, operator), the holding period (ten years by convention), the terminal capitalisation rate applied to year-eleven income and the brokerage and legal costs at sale.
3. **Calculate total property value.** The tool deducts annual debt service (loan x mortgage constant) from net income to give the equity cash flows, computes the equity residual (net reversion less the loan balance), discounts both at the equity yield and adds the loan. With the loan sized on LTV it solves the simultaneous valuation formula in closed form; with the loan fixed by DCR or debt yield it values directly. It reports value, loan, equity, the equity cash flows, the residual, the going-in cap rate, value per key and an IRR check that must equal the equity yield.
4. **Reasonableness.** Going-in cap rate against transaction evidence; terminal rate above the going-in rate; value per key against precedents (`precedent_transactions`); an unlevered DCF at the WACC (`compute_wacc`, `dcf_valuation`) within a defensible band of the mortgage-equity value; debt service covered in every year (the tool warns when it is not).

### Phase 5. Feasibility: residual land value and returns

Tools: `residual_land_value`, `dcf_sensitivity`, `lbo_returns`, `build_football_field`, `financial_calculator`.

1. **Residual land value.** For a greenfield project the tool defers the stabilised HMEV value to today over the construction and ramp-up period, then deducts hard costs, site works, soft costs, FF&E and OS&E, pre-opening and working capital, contingency, construction financing and the required developer profit on cost. The result is the maximum justifiable land acquisition cost; against the asking price it reports headroom and profit on cost at that price.
2. **Cash-flow residual and reconciliation.** Where the sales or ramp-up timeline is long, build the dated development cash flow and solve for the land value that delivers the target unlevered IRR with `financial_calculator`; explain any difference from the static residual by timing.
3. **Returns to the capital structure.** Total investment (with and without land and finance), peak equity, unlevered project IRR, leveraged equity IRR, equity multiple, payback, stabilised NOI (after the reserve), yield on cost, profit on cost, DSCR through ramp-up and break-even occupancy. The equity waterfall is modelled exactly as the shareholders' or LP agreement drafts it.
4. **Sensitivities and scenarios.** At minimum: penetration index and ADR index plus and minus 10 percent (through the RNAADR), occupancy plus and minus 5 points, hard costs plus and minus 10 percent, equity yield and terminal cap rate plus and minus 100 and 50 basis points, mortgage rate plus 100 basis points, construction delay of 6 and 12 months. Present base, downside and upside cases.
5. **Decision test.** If the asking land price exceeds the residual, state the ADR, penetration or cost change needed to close the gap and whether the market evidence supports it. The gap is never closed by raising assumptions without new evidence.

### Phase 6. Sanity checks and validation gates

The agent does not release a figure to an IM draft until each gate is passed or the exception is documented in the assumptions register.

| Gate | Test | Action on failure |
|---|---|---|
| Penetration | Stabilised overall penetration below 1.3x fair share, each segment index evidenced | Lower the indices or document the product and brand evidence |
| Latent demand | Every unaccommodated and induced demand entry has a named source | Set unevidenced latent demand to zero |
| Statement ratios | GOP margin, NOI margin and NOI per available room inside comp-set ranges | Revisit the base statement and fixed shares |
| Debt sizing | Loan equals the most restrictive of LTV, DCR and debt yield; debt service covered in every projection year | Resize the loan; report the effect on value and equity |
| IRR check | HMEV equity IRR equals the equity yield; unlevered DCF within a defensible band of the HMEV value | Reconcile the inputs before reporting either value |
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
4. **Location and supply and demand dynamics.** Proximity to primary demand generators, the competitive set with base-year penetration indices, the RNAADR supply additions and demand growth, the subject's projected penetration, occupancy, ADR and RevPAR, and the validation tests passed in Phase 1.
5. **Business plan.** The ten-year FIXVAR operating pro forma (occupancy, ADR, RevPAR, departmental revenues and expenses, GOP, management fees, fixed charges, reserve, NOI), residential sales schedule and pricing, operator and brand terms, operating structure.
6. **Development plan and budget.** Capital expenditure by category, cost per sqm and per key benchmarks, programme with milestones, procurement strategy, permitting status and risks, contingency policy.
7. **Financial projections and returns.** Sources and uses, funding timeline, debt underwriting criteria, the HMEV value bridge (loan, equity cash flows, residual), total investment, leveraged IRR, equity multiple, payback, stabilised NOI, residual land value, sensitivity tables and scenarios, football field.
8. **Exit strategy.** Hold period, exit route (single-asset sale to an institutional hotel investor, sale with residences sold out, refinancing and hold), the terminal capitalisation rate with transaction evidence, forecast net sales proceeds after brokerage and legal costs, and the loan balance repaid at sale.
9. **Risk factors and mitigants.** Planning, construction, cost inflation, market, operator, financing, FX and regulatory risks, each with mitigant and the sensitivity result that quantifies it.
10. **Structure, governance and terms.** Vehicle, governance rights, fees, waterfall, reporting, key-person and exit provisions.
11. **Appendices.** Assumptions register, comp set detail, cost plan summary, model outputs, team biographies, legal and technical due diligence summaries, disclaimer.

The agent drafts sections 1, 4, 5, 7, 8 and 9 in full from the model and the register, drafts 3 and 6 from the data room with gaps flagged, and leaves 2, 10 and the biographies for the deal team, offering structure and prompts.

### Phase 8. Investor teaser and outreach

1. **Teaser (maximum three pages).** Page 1: location, concept and the single image that explains the site; page 2: masterplan summary and unique selling propositions; page 3: KPI table (total capex, equity requirement, IRR, equity multiple, stabilised EBITDA, timeline) and the ask. No assumption appears in the teaser that is not in the IM.
2. **Proposal email.** Tailored to the recipient's mandate (core-plus hotel investor, family office, operator-investor, development lender). Four parts: why this partner, what is being offered (JV or equity ticket, preferred return hurdle, promote and waterfall structure, governance), targeted returns with the risk framing, and a specific call to action (site visit dates or NDA execution for the full IM). Length under 250 words.
3. **Compliance.** Forward-looking statements carry the firm's disclaimer; returns are "targeted", never "expected" or "guaranteed"; confidential material goes out only after NDA; the agent checks the draft against the compliance manual before release and flags anything it cannot verify.

### Phase 9. Trainee mentorship and educational scaffolding

1. **Model annotations.** Every section of the RNAADR, FIXVAR and HMEV workbooks carries a short note: what the block computes, the formula (the fixed and variable calculation, the market share adjuster, the simultaneous valuation formula), the source of each input and the common error it guards against (for example, applying the variability index in nominal rather than real terms, discounting the reversion at the wrong period, double counting the reserve).
2. **Assumption justifications.** The assumptions register's rationale column is written for a junior reader: why a given natural vacancy or stabilised occupancy was selected, how new supply additions change the unaccommodated demand calculation, why scarcity supports the ADR index, why the equity yield carries a country or stage premium, why the contingency is sized as it is.
3. **Methodology primers.** One page each on the residual method (static and cash flow), DCF versus income capitalisation, FCFE and the equity waterfall, and the difference between project and equity IRR.
4. **Case studies.** Each closed or declined project becomes an anonymised case: brief, data pack, RNAADR, FIXVAR and HMEV workbooks, memorandum extract, the committee's decision and the lessons. Recommended order for the first set: (i) a coastal resort with branded residences, the firm's core product, which exercises the full RNAADR to residual chain; (ii) an urban mixed-use repositioning, which introduces existing-income analysis, a commercial and meeting demand mix and refurbishment phasing; (iii) a marina-led master plan, which adds infrastructure phasing and ancillary income. Joint venture structures to pair with them: a straight pari passu equity JV, a preferred equity with a promote over an 8 percent hurdle, and a land-for-equity contribution by the vendor.
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
| R-02 | Stabilised ADR index by segment | | x market | | | | | |
| R-03 | Stabilised penetration index by segment | | x fair share | | | | | |
| R-04 | Unaccommodated demand by segment | | percent of base | | | | | |
| R-05 | Branded villa price | | EUR per sqm | | | | | |
| C-01 | Hard cost, hotel | | EUR per sqm GFA | | | | | |
| C-02 | Contingency | | percent of hard cost | | | | | |
| F-01 | Terminal capitalisation rate | | percent | | | | | |
| F-02 | Equity yield rate | | percent | | | | | |
| F-03 | Mortgage rate, amortisation, LTV, DCR, debt yield | | | | | | | |
| F-04 | Construction LTC and rate | | percent | | | | | |

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
| Terminal cap rate and net sales proceeds | | | |
| HMEV value, loan and equity | | | |
| Residual land value versus asking price | | | |

## Appendix 3. Glossary

ADR average daily rate; HARC historic average room count; RNAADR room-night analysis and ADR forecast; FIXVAR fixed and variable component forecast; HMEV hotel mortgage-equity valuation; DCR debt coverage ratio; RevPAR revenue per available room; TRevPAR total revenue per available room; GOP gross operating profit; NOI net operating income; FF&E furniture, fixtures and equipment; OS&E operating supplies and equipment; GDV gross development value; TDC total development cost; RLV residual land value; LTC loan to cost; LTV loan to value; DSCR debt service coverage ratio; FCFE free cash flow to equity; MOIC multiple on invested capital; HMA hotel management agreement; MICE meetings, incentives, conferences and exhibitions; USALI Uniform System of Accounts for the Lodging Industry.

---

*Analytical support for VT Capital Asset Management's internal decision-making. Not investment advice, a valuation report under the RICS Red Book, or a fairness opinion.*
