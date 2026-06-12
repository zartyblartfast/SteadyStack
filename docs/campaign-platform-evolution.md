# SteadyStack Campaign Platform Evolution Plan

> **Purpose:** Preserve the product/design evolution from the current fee-aware DCA prototype into the campaign-based SteadyStack platform.

**Status:** Planning document. No production implementation has started yet.

**Current baseline:** `main` at `33e3678` is the v0.2 fee-aware advisory prototype.

**Design artifacts:** Disposable HTML sketches currently live in `/tmp/SteadyStack-inspect/sketches/`, with the refined second round under `/tmp/SteadyStack-inspect/sketches/v2/`.

---

## 1. Why we are not wiping `main`

The existing `main` branch is still useful. It contains:

- FastAPI backend structure
- Next.js/Tailwind frontend scaffold
- BFF proxy pattern
- current fee monitor and fee-history ideas
- backtesting/evidence work
- projection tool
- tests
- docs and ADR history

The product direction has changed, but the repo does not need to be reset. Treat `main` as the last stable prototype and evolve on a new branch.

Recommended branch:

```bash
git checkout -b feature/campaign-platform
```

---

## 2. Product direction

SteadyStack is evolving from a single fee-checking DCA dashboard into a campaign-based Bitcoin accumulation platform.

Core principles:

1. DCA is the foundation.
2. Users should not try to time the bottom.
3. Fee optimisation is default for every campaign.
4. BMRI is optional per campaign and used as value/regime context, not as an automated trading signal.
5. Users can run multiple campaigns in parallel.
6. Campaign reporting/history is first-class.
7. Advisory mode comes first.
8. Hosted/VPS monitoring is likely needed for reliable alerts for normal laptop users.
9. Automation comes later, using restricted exchange API keys with trade-only permission and withdrawals disabled.
10. Users must be shown exactly what is stored/transmitted and what is never stored.

---

## 3. Campaign types

### 3.1 Core DCA

Purpose: ongoing accumulation.

- BMRI off by default, but BMRI remains visible as context.
- Adaptive fee optimisation included.
- Can run indefinitely or until the user stops it.
- Advisory first; automation later.

### 3.2 Bear Market Boost

Purpose: buy extra when Bitcoin is historically cheap.

- BMRI enabled.
- Default trigger: P10 value zone.
- P10 means the BMRI reading is in the cheapest 10% of historical readings in the available dataset, relative to long-term Bitcoin value anchors.
- P5 marks deeper value.
- Typical duration: 3–5 months.
- If BMRI rises above threshold early, alert user and offer continue / pause / stop.
- Advisory-first is recommended.

### 3.3 Fixed-Term DCA

Purpose: deploy a planned USD allocation over a defined period.

Example:

- $200/month for 12 months = $2,400 total planned allocation.

Properties:

- fixed budget and end date
- adaptive fee optimisation included
- BMRI optional/contextual
- completion report included

---

## 4. Adaptive fee optimisation

Fee optimisation should not be presented like a generic wallet priority selector.

Instead of asking users to choose high/medium/low priority, SteadyStack should recommend a realistic low-fee target based on:

- current mempool state
- recent fee history
- daily/weekly low-fee patterns
- campaign cadence
- market/fee regime
- planned buy amount

The recommended sat/vB target adapts over time.

Examples:

- Quiet market: 1 sat/vB may be realistic for weekly DCA.
- Bull/high-fee market: 4+ sat/vB may be the realistic low-fee target.

The app should show:

- recommended sat/vB
- estimated confirmation time/range
- estimated USD network fee
- estimated fee as % of planned buy
- reason for recommendation
- when the target was last recalculated

Important: fee as % of planned buy is critical. A fee that is acceptable for a $1,000 buy may be unacceptable for a $20 buy.

Campaign guardrails should support:

- max sat/vB
- max estimated fee USD
- max fee as % of buy amount

Default user-facing guardrail should probably be percentage-based, e.g.:

> Pause/review if estimated network fee exceeds 2% of this buy.

Campaigns may:

- warn
- require confirmation
- pause

if the adaptive realistic fee target exceeds guardrails.

Fee target changes must be logged and visible in campaign reports.

Example event:

> Core Stack changed from 1 → 2 sat/vB because recent weekly lows moved higher.

---

## 5. BMRI usage

Use percentile terminology:

- P10
- P5
- P50
- P90

Avoid Q10/Q5.

Always define BMRI in UI:

> BMRI means Bitcoin Mean Reversion Index: a percentile measure of Bitcoin price relative to long-term value anchors.

BMRI should be used as:

- campaign trigger/context
- value-zone charting
- reporting context

BMRI should not be presented as:

- guaranteed buy signal
- bottom predictor
- automated trading signal

BMRI is still useful even for campaigns where BMRI is not enabled. For example, a Core DCA user may still want to know whether the current market is P50 or P90.

---

## 6. Monitoring and execution modes

Separate monitoring from execution.

### Monitoring modes

1. This device only
   - private/local
   - only reliable while app/device is running

2. Hosted advisory monitor
   - practical default for laptop users
   - watches public Bitcoin metrics and campaign rules
   - sends alerts
   - requires transparent data inventory

3. Self-hosted agent
   - for advanced users running their own server/VPS/home server

### Execution modes

1. Advisory/manual
   - user receives recommendation
   - user executes manually
   - user may mark buy complete

2. Approval-required automation
   - later feature
   - system proposes action
   - user approves before execution

3. Automated
   - later feature
   - executes within strict user-defined limits

---

## 7. Automation security model

Automation should come after advisory monitoring is solid.

Recommended starting point:

- user keeps funds on exchange
- user provides restricted exchange API key
- key has trade permission only
- withdrawals disabled
- IP-whitelisted to SteadyStack server where supported
- SteadyStack can buy BTC within limits
- SteadyStack cannot withdraw funds

This avoids server-held wallets, seed phrases, private keys, or withdrawal authority.

Worst-case breach should be limited to bad trades within guardrails, not direct theft/withdrawal.

Automation requires:

- permission validation
- rejection of withdrawal-enabled keys
- spend caps
- per-buy limits
- daily/weekly/monthly limits
- fee guardrails
- audit logs
- emergency pause
- notification after every action
- clear disclosure of stored/transmitted data

---

## 8. Data transparency and ownership

Users need clear privacy/security disclosure.

For hosted advisory monitoring, the service may store:

- campaign rules
- BMRI thresholds
- fee guardrails
- alert preferences
- campaign state
- optional buy history/reports

It should not store:

- seed phrases
- private keys
- withdrawal-enabled credentials
- full wallet history
- unnecessary Bitcoin addresses

UI should include:

- export backup
- import backup
- delete hosted data
- clear data inventory
- audit log

---

## 9. UI sketch direction

Current refined sketch set:

- `/tmp/SteadyStack-inspect/sketches/v2/001-overview/index.html`
- `/tmp/SteadyStack-inspect/sketches/v2/002-templates/index.html`
- `/tmp/SteadyStack-inspect/sketches/v2/003-workspace/index.html`

Live preview while the temporary server is running:

- `http://187.124.210.10:8080/v2/`

Sketch 1: Overview

- DCA into Bitcoin without trying to time the bottom
- adaptive fee optimisation
- BMRI value zones
- hosted alerts without wallet custody
- optional automation without withdrawal access
- privacy clarity

Sketch 2: Campaign Templates

- Core DCA
- Bear Market Boost
- Fixed-Term DCA
- app-recommended fee target
- P10/P5 explanation
- hosted/advisory/guardrail preview

Sketch 3: Campaign Workspace

- campaign cards
- selected campaign editing
- adaptive fee target
- fee % guardrails
- alert history
- BMRI chart overlays
- reporting
- automation trust section

---

## 10. Recommended implementation phases

### Phase 0: Preserve design artifacts

Objective: commit the planning/design direction before implementation.

Tasks:

1. Move refined sketches into repo docs, e.g. `docs/ui-sketches/campaign-ui-v2/`.
2. Keep this planning document at `docs/campaign-platform-evolution.md`.
3. Commit both on a feature branch.

### Phase 1: Bitcoin Card adapter

Objective: make Bitcoin Card the metrics source.

Tasks:

1. Add `BITCOIN_CARD_BASE_URL` config.
2. Add backend adapter for `/api/summary`.
3. Add backend adapter for `/api/bmri-comparison`.
4. Add tests with mocked Bitcoin Card payloads.
5. Expose backend endpoints for general metrics and BMRI history.

### Phase 2: Campaign domain model

Objective: introduce campaign-shaped data without replacing all UI at once.

Tasks:

1. Define campaign schemas/types.
2. Define campaign states.
3. Define campaign event/message types.
4. Define fee policy and adaptive fee target snapshot structures.
5. Add local persistence plan.

### Phase 3: Adaptive fee policy

Objective: replace wallet-style priority fee thinking with SteadyStack recommendations.

Tasks:

1. Implement fee target recommender.
2. Include estimated USD fee and % of buy.
3. Add guardrail evaluation.
4. Add fee target adjustment events.
5. Add tests for low-fee, elevated-fee, and small-buy scenarios.

### Phase 4: Campaign UI

Objective: implement the new app surface.

Tasks:

1. Build campaign templates page.
2. Build campaign workspace page.
3. Build BMRI chart overlays.
4. Build report panel.
5. Build alert/action history.

### Phase 5: Hosted advisory monitor

Objective: reliable alerts without automation.

Tasks:

1. Add scheduler/monitoring service.
2. Add notification adapters.
3. Add hosted data inventory page.
4. Add export/delete controls.
5. Add audit log.

### Phase 6: Automation later

Objective: add restricted exchange automation after advisory is proven.

Tasks:

1. Add exchange integration with trade-only keys.
2. Validate permissions and reject withdrawal-enabled keys.
3. Add IP whitelist guidance.
4. Add spend/fee guardrails.
5. Add approval-required mode before full automation.

---

## 11. Round 2 sketch appraisal and risks

The v2 sketch set is a strong direction, especially:

- Clear narrative: DCA first, optimise second.
- Three-page journey: overview → templates → workspace.
- Trust model: advisory-first, hosted alerts, trade-only exchange keys later, withdrawal keys rejected.
- Jargon handling: BMRI/P10/sat-vB tooltips and glossary.
- Honest caveats around illustrative charts.
- Consistent dark Bitcoin-themed visual system.

Key risks to address before production:

1. BMRI/P10 cognitive load
   - Do not lead normal users with `BMRI P9` or `P10 value zone` alone.
   - Add a plain-language layer first, e.g. "Bitcoin looks historically cheap right now".
   - Keep percentile detail secondary.

2. Fee optimisation framing
   - sat/vB and USD examples are useful but can make savings look small.
   - Lead with fee as % of planned buy, e.g. "fee ≈ 0.4% of this $100 buy".
   - Show USD and sat/vB as supporting detail.

3. Workspace god-page risk
   - The sketch combines create, edit, monitor, report, guardrails, charts, and automation trust.
   - Production likely needs decomposition: campaign list → campaign detail → edit wizard/report tabs.

4. Missing states
   - Add empty state for new users with zero campaigns.
   - Add error states: failed API key, exchange outage, Bitcoin Card unavailable, missed alert, paused campaign, fee guardrail exceeded.
   - Add mobile layout pass.

5. Evidence/compliance risk
   - The accumulation comparison chart is persuasive but must be backed by real backtest methodology before shipping.
   - Keep visible caveats until real evidence is wired in.

6. Sketch implementation detail
   - Duplicate CSS is fine for disposable sketches only.
   - Do not copy/paste sketch CSS structure directly into production.

## 12. Round 3 sketch direction

Round 3 addresses the v2 appraisal directly.

Design artifacts:

- `docs/ui-sketches/campaign-ui-v3/001-empty-start/index.html`
- `docs/ui-sketches/campaign-ui-v3/002-campaign-detail/index.html`
- `docs/ui-sketches/campaign-ui-v3/003-mobile-bad-day/index.html`

Goals:

1. Empty/new-user state
   - Avoid a dead-end "no campaigns" page.
   - Use "Start a Bitcoin dollar-cost averaging campaign in a few minutes."
   - Explain value in simple steps.
   - Lead to campaign creation.

2. Campaign detail split
   - Avoid the v2 workspace becoming a god-page.
   - Use campaign list → selected campaign detail → edit/report tabs.
   - Keep charts below the decision.
   - Lead BMRI with plain language: "Bitcoin looks historically cheap"; keep percentile detail secondary.

3. Mobile bad-day states
   - Show recovery flows for market data downtime, exchange permission issues, missed alerts, fee guardrail pauses, and paused campaigns.
   - Mobile rule: one decision per screen.
   - Use safe actions: retry, view cached data, reconnect key, use advisory mode, keep paused.

Round 3 design lessons:

- For new users, expand DCA at least once as "dollar-cost averaging".
- Do not expose "empty state" / "bad day" labels as user-facing copy.
- Lead fee displays with fee as % of planned buy; sat/vB and USD are supporting details.
- For BMRI, plain language first, model detail second.
- Global/other-campaign alerts should be labelled separately from the selected campaign.
- Production workspace should likely be decomposed into list, detail, edit wizard, report, and charts rather than one large page.

Round 3 appraisal:

- Plain-language BMRI layer works: lead with "Bitcoin looks neutral today" / "Bitcoin looks historically cheap right now"; keep P43/P9/P10 as secondary detail.
- Fee framing works: lead with fee as % of planned buy; sat/vB and USD are supporting figures with caveats.
- Empty start page is a good first-run experience: 3-step path, no blank form, trust panel showing stored / never stored / later automation.
- Campaign detail split resolves the v2 god-page risk. The guardrail rule and report counters make the system auditable.
- Bad-day/mobile sketch is strong and should inform the real spec: realistic failure taxonomy, safe degradation, one or two actions per error state.
- "One decision per screen" should become a product/spec rule for mobile.

Remaining product decisions before implementation:

1. Missed-alert state
   - Consider showing what was missed, e.g. estimated savings, but avoid nagging.
   - Example: "You may have saved about $0.70" only when useful and clearly estimated.

2. Mobile happy path
   - V3 covers mobile alerts/errors, but not normal mobile campaign list/detail.
   - Either add one small mobile happy-path sketch or include it directly in the build spec.

3. Max-wait / fee-deadline rule
   - A campaign must not wait forever for 1 sat/vB in a busy mempool.
   - Add a user-set rule such as: "If the target is not reached after X days, buy anyway at the best available fee within guardrails".
   - This should live alongside adaptive fee target and fee guardrails.

4. Guardrail units
   - Keep fee guardrail units consistent.
   - If a buy is $100, 2% is $2, not $5.
   - UI should clearly show derived equivalents when multiple guardrails are displayed.

V3 verdict:

The design direction is complete enough to stop broad sketching and start writing the real product/build specification. Further sketching should be limited to the mobile happy path or specific unresolved product decisions.

## 13. Immediate next recommendation

The design artifacts are now committed on `feature/campaign-platform`:

```bash
git checkout feature/campaign-platform
```

Committed files:

- `docs/campaign-platform-evolution.md`
- `docs/ui-sketches/campaign-ui-v2/`
- `docs/ui-sketches/campaign-ui-v3/`

Do not modify production app code until the design direction and next-state sketches are agreed.
