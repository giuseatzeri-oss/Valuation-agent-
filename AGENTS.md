# AGENTS.md

<!-- handoff:learnings:begin -->
## Session Learnings (auto-updated by handoff)

### Implicit Rules
- User communicates in Italian; deliverables in Italian
- Work branch: claude/feem-catalog-analysis-5batmn; no PR unless asked
- MLOL login credentials were supplied in chat by the user; never commit them
- Scratchpad crawl data: crawl.json, details.json, state.json under session scratchpad mlol/ (ephemeral)

### Key Decisions
- Decision: create personal env 'Valuation-agent (MLOL access)' allowing only medialibrary.it hosts — Reason: Default env proxy returned 403; minimal host set
- Decision: Playwright with storageState in scratchpad — Reason: site uses altcha anti-bot challenge; credentials never written to repo
- Decision: crawl all titles at size=96 (max) ordered by title — Reason: theme taxonomy unreliable, need full list for keyword search
- Decision: manual 3-tier ranking, exclude generalist/lifestyle/consumer travel titles — Reason: focus on valuation-relevant sources (PE, RE, hospitality, financial dailies)

<!-- handoff:learnings:end -->
