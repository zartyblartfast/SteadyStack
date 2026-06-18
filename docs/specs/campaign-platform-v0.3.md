# SteadyStack Campaign Platform v0.3 Specification

> **Status:** Implementation-ready draft. Broad product/spec polish should stop here unless a Phase 2/3 implementation review finds a blocking issue.
>
> **Branch:** `feature/campaign-platform`
>
> **Related docs:**
> - `docs/campaign-platform-evolution.md`
> - `docs/ui-sketches/campaign-ui-v2/`
> - `docs/ui-sketches/campaign-ui-v3/`
>
> **Goal:** Evolve SteadyStack from a single fee-aware DCA dashboard into a campaign-based Bitcoin accumulation platform with adaptive fee optimisation, optional BMRI value campaigns, campaign reporting, and advisory-first monitoring.

---

## 1. Product thesis

SteadyStack helps users accumulate Bitcoin through disciplined dollar-cost averaging without trying to time the bottom.

DCA is the foundation. SteadyStack improves DCA by:

1. recommending realistic low-fee purchase windows,
2. adapting fee targets as mempool conditions change,
3. optionally starting extra value campaigns when Bitcoin appears historically cheap via BMRI,
4. giving users campaign-level reports and audit history,
5. providing advisory alerts first, with carefully scoped automation later.

SteadyStack should not feel like a trading dashboard. It should feel like a calm Bitcoin accumulation planner.

---

## 2. v0.3 scope

### 2.1 In scope

v0.3 should define and begin implementing:

- Bitcoin Card metrics integration.
- Campaign-based data model.
- Campaign templates:
  - Core DCA
  - Bear Market Boost
  - Fixed-Term DCA
- Adaptive fee target policy.
- Fee guardrails based on:
  - sat/vB
  - estimated USD fee
  - fee as % of planned buy
- BMRI value-zone context and triggers.
- Campaign event/audit log.
- Campaign reports.
- Advisory-first UI flow.
- Empty/new-user state.
- Error/bad-day states.
- Export/import awareness for user-owned data.

### 2.2 Out of scope for first v0.3 implementation

Do not implement yet:

- full exchange automation,
- hosted credential storage,
- auto-withdrawal,
- seed/private-key handling,
- wallet signing,
- multi-user hosted backend billing,
- mobile app.

The design should remain compatible with later automation, but the first build should be advisory-first.

---

## 3. Core concepts

### 3.1 Campaign

A campaign is a user-defined Bitcoin accumulation plan.

A user may run multiple campaigns in parallel, e.g.:

- Core DCA: ongoing weekly accumulation.
- Bear Market Boost: extra DCA when Bitcoin looks historically cheap.
- Fixed-Term DCA: deploy a fixed USD amount over a fixed period.

Each campaign has its own:

- budget,
- cadence,
- status,
- fee policy,
- BMRI settings,
- monitoring mode,
- execution mode,
- report,
- event history.

### 3.2 Monitoring mode

Monitoring answers: who watches metrics and sends alerts?

Supported conceptual modes:

1. `local_device`
   - Works only while the app/device is running.
   - Maximum privacy.
   - Not reliable for most laptop users.

2. `hosted_advisory`
   - Hosted/VPS monitor checks campaign rules and public Bitcoin metrics.
   - Sends user alerts.
   - Does not need wallet custody, private keys, or withdrawal access.
   - Practical default for mainstream users.

3. `self_hosted_agent`
   - Advanced user runs their own always-on monitor.

v0.3 may implement only local/manual behavior initially, but the data model should preserve this distinction.

### 3.3 Execution mode

Execution answers: who actually performs the buy?

1. `advisory_manual`
   - SteadyStack recommends.
   - User buys manually.
   - User can mark buy complete.

2. `approval_required_automation`
   - Future mode.
   - SteadyStack prepares action.
   - User confirms before execution.

3. `automated_limited`
   - Future mode.
   - SteadyStack executes within strict limits.

v0.3 should default to `advisory_manual`.

## 3.4 Persistence and auth model

For v0.3, use a backend-owned persistence model rather than browser-only localStorage.

Recommended local/dev persistence:

- SQLite for local development and single-user deployments, or PostgreSQL when running in hosted mode.
- Frontend consumes backend APIs; the browser should not be the source of truth for campaigns/events/reports.

Why:

- campaign events and reports need durable storage,
- hosted advisory monitoring needs server-side campaign rules,
- future automation/audit logs need backend persistence,
- export/import can be implemented from backend-owned data.

For advisory-only local mode, auth can remain minimal during early development. For hosted advisory mode, add account/auth before storing real user campaign data remotely.

Export/import requirements:

- export campaigns, fee policies, BMRI policies, events, buy records, and reports;
- include schema version and exported timestamp;
- allow import preview before applying;
- support replace vs merge later.

Known v0.3 constraint: currency is USD-only unless explicitly expanded later.

---

## 4. Campaign templates

### 4.1 Core DCA

Purpose: ongoing Bitcoin accumulation.

Default behavior:

- BMRI off as a trigger.
- BMRI still visible as context.
- Adaptive fee target enabled.
- Indefinite until user pauses/stops.
- Advisory manual execution.

User-facing summary:

> Buy consistently while SteadyStack watches for realistic low-fee windows.

### 4.2 Bear Market Boost

Purpose: extra accumulation when Bitcoin appears historically cheap.

Default behavior:

- BMRI trigger enabled.
- Entry threshold: P10.
- Deep value marker: P5.
- Suggested duration: 3–5 months.
- Advisory-first.
- Fee optimisation still applies.

Plain-language UI:

> Bitcoin looks historically cheap right now.

Secondary detail:

> BMRI P9, inside your P10 value zone.

P10 definition:

> P10 means the BMRI reading is in the cheapest 10% of historical readings in the available dataset, relative to long-term Bitcoin value anchors.

### 4.3 Fixed-Term DCA

Purpose: deploy a planned USD amount over a defined period.

Example:

> $200/month for 12 months = $2,400 total planned allocation.

Default behavior:

- fixed total budget and end date,
- adaptive fee target enabled,
- BMRI optional/contextual,
- completion report included.

---

## 5. Bitcoin Card metrics integration

Bitcoin Card is SteadyStack's normal-path metrics source. If SteadyStack needs a Bitcoin metric that Bitcoin Card does not expose, enhance Bitcoin Card first rather than adding another direct source to SteadyStack.

### 5.1 Local HTTP endpoints

Base URL default:

```text
http://127.0.0.1:8787
```

Relevant endpoints:

- `GET /api/summary`
- `GET /api/bmri-comparison`

### 5.2 MCP option

Bitcoin Card also exposes MCP tools, but the current web app should initially integrate through HTTP.

Primary tools for future agent workflows:

- `get_dca_metrics`
- `get_bitcoin_mean_reversion_index`
- `get_network_summary`
- `get_mempool_fees`
- `get_fee_history`

### 5.3 SteadyStack adapter responsibility

Create a backend adapter that normalizes Bitcoin Card payloads into internal types.

The adapter should expose:

- current BTC price,
- fee tiers,
- network state,
- BMRI latest values,
- BMRI history,
- source/caveat metadata,
- fetched timestamp.

### 5.4 Caveats

The UI must show:

- fetched time,
- source names,
- BMRI caveats,
- whether Full BMRI or BMRI-lite is being used.

Do not present BMRI as a guaranteed signal.

### 5.5 Metrics fallback and stale data behavior

Bitcoin Card is a critical dependency for the new metrics flow. SteadyStack must define safe behavior when it is unavailable.

Rules:

- Cache the last successful metrics payload with `fetchedAt`.
- Mark metrics stale when older than the configured stale threshold.
- If fee data is stale, do not issue new buy recommendations.
- If BMRI data is stale, do not trigger new Bear Market Boost campaigns.
- If a campaign is already active and metrics become stale, move it to `needs_review` or `paused` depending on severity.
- If Bitcoin Card is unavailable for days, keep campaigns safe and show a clear bad-day state: "Market data unavailable; campaigns paused until fresh data is available."

Suggested initial thresholds:

- fee data stale after 30 minutes,
- price/network summary stale after 60 minutes,
- BMRI latest stale after 24 hours,
- BMRI history stale after 7 days for charting only.

Cached data may be displayed with a stale badge, but should not silently drive new actions.

### 5.6 Bitcoin Risk and DCA metrics context

Bitcoin Card now exposes Bitcoin Risk through both MCP and local HTTP. This should inform SteadyStack's future charting and campaign context.

Relevant surfaces:

- MCP `get_dca_metrics`: compact app bundle with price, fees, network state, BMRI zone/caveat, and Bitcoin Risk proxy.
- MCP `get_bitcoin_risk`: full Bitcoin Risk payload.
- HTTP `GET /api/bitcoin-risk`: full Bitcoin Risk composite payload.

Bitcoin Risk fields of interest:

- `metric`: `bitcoin-risk-composite`.
- `riskScore`: 0-100 composite risk score.
- `band`: `deep_value`, `value`, `neutral`, `elevated`, `high`, or `extreme`.
- `components`: component breakdown with `value`, normalized `score`, `sourceMetric`, and `methodology`.
- `components.mvrvZDerived`: MVRV-Z-derived valuation component.
- `components.puellIssuance`: Puell-style issuance multiple.
- `components.mayerMultiple`: Mayer Multiple.
- `components.ma200wDistance`: daily approximation of 200-week moving-average distance.
- `history[]`: daily points with `date`, `unixTs`, `mvrv`, `mvrvZScore`, `components`, `riskScore`, and `band`.
- `sentiment`: optional Alternative.me Fear & Greed context; separate from `riskScore` and attribution-required if shown.
- `source.sourceQuality`, `methodology`, `limitations`, `fetchedAt`, and `dataDate`.

Product decision for v0.3:

- Do not use Bitcoin Risk as an automatic campaign trigger yet.
- Treat it as valuation context alongside BMRI.
- Do not blend BMRI and Bitcoin Risk into one opaque score in v0.3.
- If both metrics are shown, explain agreements/disagreements plainly.
- Label Bitcoin Risk clearly as bitcoin-card's transparent native composite; it is not Cowen Risk, not Glassnode-equivalent, not entity-adjusted, not proprietary, and not a trading signal.
- Sentiment remains separate market context and must not be blended into valuation risk.

Future chart requirement:

Use a stacked valuation chart rather than a crowded single-axis overlay:

1. BTC price, preferably log scale.
2. BMRI full/lite index, 0-100 scale.
3. Bitcoin Risk score, 0-100 scale.

Use shared x-axis and campaign overlays across panels. Add optional component charts for Bitcoin Risk when the user expands details. Sentiment, if shown, should be a separate annotation/context layer, not part of valuation risk.

---

## 6. Adaptive fee optimisation

### 6.1 Product rule

Fee optimisation is default for every campaign.

Do not make users choose generic wallet priority tiers as the primary flow.

Instead, SteadyStack recommends a realistic low-fee target for the campaign's cadence and current fee regime.

### 6.2 User-facing hierarchy

Lead with:

1. fee as % of planned buy,
2. estimated USD network fee,
3. sat/vB target,
4. estimated confirmation range.

Example:

> Fee is about 0.4% of this $100 buy.
>
> Target: around 1 sat/vB, roughly $0.90 in this example.

### 6.3 Inputs

The fee recommender should consider:

- Bitcoin Card fee tiers,
- fee history,
- current mempool state,
- campaign cadence,
- planned buy amount,
- estimated transaction size,
- current BTC price,
- recent low-fee windows.

### 6.4 Outputs

A fee recommendation should include:

- recommended sat/vB,
- estimated fee USD,
- estimated fee as % of buy,
- estimated confirmation range,
- regime label,
- reason text,
- confidence,
- calculated timestamp.

### 6.5 Adaptive target changes

The target can change during a campaign.

Example event:

> Core Stack changed from 1 → 2 sat/vB because recent weekly lows moved higher.

Every change should be logged and shown in campaign reporting.

### 6.6 Guardrails

Campaign fee guardrails should support:

- max sat/vB,
- max estimated fee USD,
- max fee as % of planned buy.

Default guardrail should likely be percentage-based.

Example:

> Pause/review if estimated network fee exceeds 2% of this buy.

Important consistency rule:

- 2% of $100 = $2.
- Do not show inconsistent derived examples like 2% and $5 together unless the buy amount makes that true.

### 6.7 Max-wait / fee-deadline rule

A campaign must not wait forever for an unrealistically low fee.

Add a user-set rule such as:

> If the target is not reached after X days, buy anyway at the best available fee within guardrails.

This rule protects the core DCA promise.

Potential fields:

- max_wait_days,
- on_deadline:
  - `buy_best_available_within_guardrails`,
  - `ask_user`,
  - `pause_campaign`,
- deadline_event_message.

### 6.8 Scheduling semantics

Campaign cadence must be anchored and deterministic.

Definitions:

- `cadence`: daily, weekly, monthly, or custom.
- `anchorDate`: the starting date/time used to calculate future intended buy periods.
- `timezone`: user-selected timezone; default to the user's locale during setup.
- `periodWindow`: the current intended DCA period, e.g. this week for weekly cadence.

Rules:

- Weekly campaigns default to the weekday/time of campaign activation unless user changes it.
- Monthly campaigns default to the day-of-month of activation, with explicit handling for short months.
- If the recommended fee target is reached during the period, generate a buy recommendation.
- If the target is not reached before `maxWaitDays` / deadline, apply `onDeadline`.
- Do not queue unlimited missed buys. A missed period should create a `missed_alert` or `period_missed` event and then advance to the next period according to campaign policy.
- If multiple periods are missed because data was unavailable, surface a review state instead of silently stacking buys.

Open product decision for implementation plan:

- Whether a missed buy rolls into the next buy amount or is skipped. Default for v0.3 should be "ask/review" rather than silent rollover.

---

## 7. BMRI rules

### 7.1 Plain language first

Do not lead normal users with:

- BMRI P9,
- P10 value zone,
- percentile jargon.

Lead with:

- "Bitcoin looks historically cheap right now."
- "Bitcoin looks neutral today."
- "Bitcoin looks expensive relative to long-term anchors."

Then show technical detail:

- BMRI P9,
- P10 threshold,
- Full BMRI vs BMRI-lite.

### 7.2 BMRI campaign trigger

For Bear Market Boost:

- default trigger: BMRI <= P10,
- deep value marker: P5,
- user can configure threshold later.

### 7.3 BMRI exit/review

If BMRI rises above threshold during an active BMRI campaign:

- do not silently stop by default,
- alert user,
- offer continue / pause / stop,
- log decision.

### 7.4 BMRI chart

BMRI chart should show:

- plain-language state,
- BMRI line,
- P10/P50/P90 reference lines,
- campaign overlays,
- buy markers,
- caveats/source.

Charts should support the decision, not be the decision UI.

---

## 8. Campaign states

Campaign status values:

- `draft`
- `waiting`
- `ready`
- `active`
- `paused`
- `needs_review`
- `completed`
- `stopped`

Examples:

- Core DCA active.
- Bear Market Boost ready because Bitcoin looks historically cheap.
- Campaign paused because fee exceeds guardrail.
- Fixed-Term DCA completed.

### 8.1 State transition table

Allowed transitions should be explicit and tested.

| From | To | Trigger | Notes |
| --- | --- | --- | --- |
| `draft` | `waiting` | user saves campaign but trigger/start condition not met | common for BMRI campaigns |
| `draft` | `active` | user starts immediately | common for Core DCA |
| `waiting` | `ready` | BMRI trigger met or scheduled start reached | requires user action in advisory mode |
| `ready` | `active` | user confirms start | log `campaign_started` |
| `active` | `paused` | user pauses, fee guardrail exceeded, stale data policy pauses | log reason |
| `active` | `needs_review` | BMRI exit, stale metrics, missed periods, guardrail warning | requires user decision |
| `active` | `completed` | fixed-term campaign reaches end/budget complete | report remains available |
| `active` | `stopped` | user stops campaign | terminal unless explicitly cloned/restarted |
| `paused` | `active` | user resumes or data/fees recover and user confirms | do not auto-resume unless policy explicitly allows |
| `paused` | `stopped` | user stops | terminal |
| `needs_review` | `active` | user chooses continue | log user decision |
| `needs_review` | `paused` | user chooses pause or system requires safe pause | log reason |
| `needs_review` | `stopped` | user stops | terminal |
| `ready` | `waiting` | user snoozes/declines trigger | e.g. wait for next trigger/check |

Disallowed by default:

- `completed` → `active`; clone or create a new campaign instead.
- `stopped` → `active`; clone or create a new campaign instead.
- silent `paused` → `active` without user confirmation, unless a future policy explicitly enables it.

Stale-data note:

- If a `waiting` campaign depends on BMRI and BMRI data becomes stale, it should remain `waiting` with a stale-data badge/event. Do not move it to `ready` until fresh BMRI data confirms the trigger.

---

## 9. Campaign events

All important campaign actions should create events.

Event examples:

- `campaign_created`
- `campaign_started`
- `campaign_paused`
- `campaign_resumed`
- `campaign_completed`
- `bmri_triggered`
- `bmri_exit_review`
- `fee_target_adjusted`
- `fee_guardrail_warning`
- `fee_guardrail_pause`
- `buy_recommended`
- `buy_marked_complete`
- `missed_alert`
- `period_missed`
- `data_source_unavailable`
- `exchange_permission_issue`

Events should include:

- timestamp,
- campaign id,
- type,
- severity,
- plain-language title,
- message,
- metric snapshot,
- available actions,
- resolved status.

---

## 10. Campaign reporting

Campaign reports should persist after a campaign ends.

Reports should answer:

- Did this campaign meet my objective?
- How much BTC did I accumulate?
- How much USD did I spend?
- What was my average price?
- What is the current value?
- What is the unrealized gain/loss?
- How much did network fees cost?
- What was the fee as % of buy volume?
- How often did fee targets change?
- Were there guardrail pauses?
- Were there missed alerts?

Report fields:

- total_usd_spent,
- btc_accumulated,
- average_purchase_price, // USD spent divided by BTC acquired; specify separately whether network fees are included in views
- current_value_usd,
- unrealized_gain_loss_usd,
- unrealized_gain_loss_pct,
- number_of_buys,
- average_fee_sat_vb,
- total_estimated_network_fees_usd,
- network_fees_pct_of_volume,
- fee_target_change_count,
- guardrail_pause_count,
- missed_alert_count.

---

## 10.1 Multi-campaign interactions

Users can run multiple campaigns at once. The system must avoid accidental over-allocation.

Rules:

- Each campaign has its own budget and guardrails.
- Add optional global user guardrails before automation: max daily spend, max weekly spend, max monthly spend, and max active campaigns.
- If multiple advisory campaigns trigger in the same period, show combined planned spend.
- For v0.3 advisory mode, do not silently merge or execute multiple campaign buys. Present a review state.
- For future automation, global spend caps must be enforced before campaign-specific actions.

---

## 11. UI architecture

### 11.1 First run / empty state

Purpose:

- avoid dead-end no-campaign page,
- explain value,
- reassure about custody,
- drive creation of first campaign.

Core copy:

> Start a Bitcoin dollar-cost averaging campaign in a few minutes.

### 11.2 Campaign templates

Purpose:

- avoid blank strategy form,
- show cloneable starting points,
- keep templates simple.

Templates:

- Core DCA,
- Bear Market Boost,
- Fixed-Term DCA.

### 11.3 Campaign list/detail

Production should avoid one large god-page.

Recommended layout:

- Campaign list.
- Selected campaign detail.
- Overview tab.
- Edit tab / wizard.
- Report tab.
- Supporting charts below the main decision.

### 11.4 Mobile

Mobile rule:

> One decision per screen.

Mobile should show:

- current alert,
- plain-language reason,
- 1–2 safe actions,
- details one layer deeper.

### 11.5 Bad-day states

Must support:

- market data unavailable,
- exchange permission issue,
- fee guardrail pause,
- missed low-fee window,
- paused campaign,
- stale data,
- hosted monitor failure.

All bad-day states must degrade safely.

---

## 12. Trust and data transparency

### 12.1 Hosted advisory

Hosted advisory monitor may store:

- campaign rules,
- alert preferences,
- BMRI/fee thresholds,
- event history,
- reports.

It should not store:

- seed phrase,
- private keys,
- withdrawal-enabled exchange keys,
- full wallet history,
- unnecessary Bitcoin addresses.

### 12.2 Automation later

Automation should use restricted exchange API keys only.

Rules:

- trade permission only,
- withdrawals disabled,
- withdrawal-enabled keys rejected,
- IP whitelist where supported,
- strict spend limits,
- fee guardrails,
- audit logs,
- emergency pause,
- notifications after every action.

User-facing copy:

> Let SteadyStack buy for you — without withdrawal access.

---

## 13. Data model draft

### 13.1 Campaign

```ts
type Campaign = {
  id: string;
  name: string;
  type: 'core_dca' | 'bear_market_boost' | 'fixed_term_dca';
  status: 'draft' | 'waiting' | 'ready' | 'active' | 'paused' | 'needs_review' | 'completed' | 'stopped';
  monitoringMode: 'local_device' | 'hosted_advisory' | 'self_hosted_agent';
  executionMode: 'advisory_manual' | 'approval_required_automation' | 'automated_limited';
  amountUsd: number;
  cadence: 'daily' | 'weekly' | 'monthly' | 'custom';
  anchorDate: string; // date/time used to calculate intended buy periods
  timezone: string; // IANA timezone, e.g. 'Europe/London'
  totalBudgetUsd?: number;
  startDate?: string;
  endDate?: string;
  feePolicy: FeePolicy;
  bmriPolicy?: BmriPolicy;
  createdAt: string;
  updatedAt: string;
};
```

### 13.2 FeePolicy

```ts
type FeePolicy = {
  adaptive: boolean;
  maxFeePctOfBuy: number;
  maxFeeUsd?: number;
  maxSatVb?: number;
  estimatedTransactionVbytes: number;
  maxWaitDays?: number;
  onDeadline: 'buy_best_available_within_guardrails' | 'ask_user' | 'pause_campaign';
};
```

### 13.3 FeeTargetSnapshot

```ts
type FeeTargetSnapshot = {
  campaignId: string;
  recommendedSatVb: number;
  estimatedFeeUsd: number;
  estimatedFeePctOfBuy: number;
  estimatedConfirmationRange: string;
  regime: 'quiet' | 'normal' | 'elevated' | 'congested' | 'extreme';
  reason: string;
  confidence: number; // 0.0 to 1.0
  calculatedAt: string;
};
```

### 13.4 BmriPolicy

```ts
type BmriPolicy = {
  enabled: boolean;
  entryPercentile: number; // default 10
  deepValuePercentile: number; // default 5
  exitPolicy: 'alert_only' | 'pause_after_review' | 'fixed_term_ignore_exit';
};
```

### 13.5 CampaignEvent

`type` should be an enum, not a free string.

```ts
type CampaignEventType =
  | 'campaign_created'
  | 'campaign_started'
  | 'campaign_paused'
  | 'campaign_resumed'
  | 'campaign_completed'
  | 'bmri_triggered'
  | 'bmri_exit_review'
  | 'fee_target_adjusted'
  | 'fee_guardrail_warning'
  | 'fee_guardrail_pause'
  | 'buy_recommended'
  | 'buy_marked_complete'
  | 'missed_alert'
  | 'period_missed'
  | 'data_source_unavailable'
  | 'exchange_permission_issue';

type CampaignEvent = {
  id: string;
  campaignId: string;
  type: CampaignEventType;
  severity: 'info' | 'success' | 'warning' | 'error' | 'action_required';
  title: string;
  message: string;
  metricSnapshot?: unknown;
  actions?: string[];
  status: 'open' | 'acknowledged' | 'resolved' | 'expired';
  createdAt: string;
  resolvedAt?: string;
};
```

---

## 14. Implementation sequence

### Phase 1: Preserve design artifacts

Done on branch `feature/campaign-platform`:

- `docs/campaign-platform-evolution.md`
- `docs/ui-sketches/campaign-ui-v2/`
- `docs/ui-sketches/campaign-ui-v3/`

### Phase 2: Bitcoin Card adapter

First real code phase.

Tasks:

1. Add config for Bitcoin Card base URL.
2. Create backend adapter module.
3. Add tests with mocked payloads.
4. Normalize summary and BMRI response types.
5. Add backend API endpoint(s) for frontend consumption.
6. Bitcoin Risk local HTTP support is implemented via SteadyStack adapter/API and surfaced in the Valuation UI.
7. Bitcoin Card fee history/profile support is implemented for the normal fee-history UI path; `/api/fees/history/{period}` now maps Bitcoin Card fee bands to the legacy chart shape, and `/api/fees/profile` exposes the patient DCA fee recommendation.

### Phase 3: Campaign domain model

Tasks:

1. Add campaign schemas.
2. Add campaign event schemas.
3. Add fee policy schemas.
4. Add BMRI policy schemas.
5. Add tests for model validation and state transitions.

### Phase 4: Adaptive fee target policy

Tasks:

1. Implement fee target recommender.
2. Include fee USD and fee % estimates.
3. Add guardrail evaluation.
4. Add max-wait/deadline handling.
5. Add tests for quiet, normal, elevated, congested scenarios.
6. Add tests for small-buy fee percentage edge cases.

### Phase 5: Campaign UI

Tasks:

1. Empty/new-user page.
2. Campaign templates.
3. Campaign list/detail.
4. Edit/report tabs.
5. Alert/event panel.
6. Mobile alert states.

---

## 15. Acceptance principles

Before production implementation is considered aligned:

- Users can understand recommendations without knowing BMRI or sat/vB.
- Technical details are available one layer deeper.
- Fee cost is shown as % of buy first.
- No campaign can silently wait forever without a deadline/guardrail policy.
- Bad data or failed permissions pause safely.
- Advisory mode requires no sensitive execution credentials.
- Automation design never requires seed phrases or withdrawal-enabled keys.
- Campaign reporting persists after completion.
- State transitions are explicit and tested.
- Campaign/event persistence is backend-owned and exportable.
