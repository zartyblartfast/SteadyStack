# SteadyStack Campaign Platform v0.3 Specification

> **Status:** Draft specification for the next major product iteration.
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

Bitcoin Card should become SteadyStack's metrics source.

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
- average_purchase_price,
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
  confidence: number;
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

```ts
type CampaignEvent = {
  id: string;
  campaignId: string;
  type: string;
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
