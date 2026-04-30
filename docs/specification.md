# Bitcoin DCA Agent — Project Specification

**Project Name:** SteadyStack  
**Version:** 1.0  
**Date:** April 2026  
**Status:** Active Development (MVP in progress)

## 1. Vision

Build a **self-sovereign Bitcoin accumulation platform** that makes disciplined DCA simple, fee-efficient, and non-custodial.

SteadyStack does not try to outsmart Bitcoin's price. Backtesting over 330 weeks of historical data (2020–2026) confirmed that no mechanical timing strategy reliably beats naive weekly DCA on cost basis. Instead, the platform focuses on what demonstrably works: **consistent accumulation**, **fee minimisation**, **self-custody**, and **education**.

**Core Promise:**  
The easiest way to DCA into Bitcoin properly — automated, fee-aware, non-custodial, and backed by real data.

### 1.1 Pillars of Value

1. **Automation without custody** — Regular Bitcoin accumulation with minimal admin. No giving custody to yet another platform. The app recommends or executes buys but never holds funds or keys.

2. **Fee-aware DCA** — Monitors mempool conditions to help users buy during low-fee windows. On-chain fees are expected to rise structurally as block subsidies halve, making fee timing increasingly valuable over time.

3. **Best-practice education** — Shows users, with historical data, why simple DCA works, why market timing mostly fails, and why fee minimisation matters. The product is part tool, part dashboard, part educational proof engine.

4. **Honest positioning** — We tested the data. Simple DCA wins. Fee savings are real but modest today. Automation and consistency are the main wins. This transparency is a commercial advantage in a space full of "AI trading" nonsense.

## 2. Design Principles

- **Deterministic decisions**: All buy/skip/wait logic is rule-based and reproducible. Given the same inputs, the engine always produces the same output. No opaque model judgment ever controls a financial decision.
- **No custody, no keys**: The tool never holds user funds, stores private keys, or has withdrawal permissions. All purchases happen through user action or user-approved exchange API calls with trading-only permissions.
- **Full auditability**: Every recommendation, execution, skip, retry, and error is logged with a timestamp, the input signals, the rules evaluated, and the outcome. Logs are immutable and user-accessible.
- **Transparency by default**: Users always see how the engine performed compared to a standard scheduled DCA strategy. No black boxes.
- **Honesty over hype**: The platform does not claim to beat the market. It claims to help users DCA efficiently while avoiding unnecessary fee drag. All performance claims are backed by historical data.

## 3. User Flows

**Free tier (manual):**
1. User opens SteadyStack dashboard — no account required.
2. Checks current fee conditions ("are fees low right now?").
3. Explores backtesting evidence and projection tools.
4. Decides when to buy and executes the buy themselves on their preferred platform.

**Automated tier:**
1. User creates account (Lightning login) and chooses a DCA profile (budget, frequency, fee sensitivity).
2. **Notification Mode**: Engine monitors fees and sends alerts when conditions are good. User buys wherever they prefer and optionally confirms the buy in the dashboard.
3. **Auto Mode**: User connects a Kraken API key (trade-only). Engine places buys automatically during low-fee windows, with or without per-buy approval depending on user preference.
4. User views **performance comparison** against naive weekly DCA on their dashboard.

## 4. How Buying Actually Works

### 4.1 Manual Mode (Free tier)
- The app shows whether fees are low/medium/high and advises whether now is a good time to buy.
- The user places any buy themselves using their own wallet or exchange. The app does not place the buy.
- Includes full access to backtesting evidence, projection tool, and educational content.
- No account required. No automation. No notifications.

### 4.2 Notification Mode (Automated tier)
- The engine monitors fees on a schedule and identifies optimal buy windows within each DCA period.
- The engine **sends a notification** (Telegram + in-app) with the recommendation and full reasoning.
- The user decides whether to act — they can buy on any exchange or service they prefer.
- The user optionally confirms the buy in the dashboard for tracking purposes.
- This mode works for users who want fee-timing intelligence but prefer to execute buys themselves (e.g. via Relai, RoboSats, or any other service).

### 4.3 Auto Mode — Approval Required (Automated tier)
- User connects an exchange API key with **trading permissions only** (no withdrawal rights).
- The engine identifies the best buy window and **sends a notification** with the recommendation.
- The engine **waits for explicit user approval** before placing the buy on the connected exchange.
- Every execution is logged with full reasoning and confirmation details.

### 4.4 Auto Mode — Fully Automated (Automated tier)
- User connects an exchange API key with **trading permissions only** (no withdrawal rights).
- The engine determines the best buy window and **places the buy automatically** within strict user-defined limits (max amount, max fee rate, etc.).
- The user is immediately notified with the reasoning and execution details after the buy is placed.
- All actions are logged and fully auditable in the dashboard.

### 4.5 Funding & Balance Management (Auto Modes only)
- Before placing any automated buy, the engine checks the exchange account balance.
- **Sufficient funds**: Proceed with buy.
- **Insufficient funds**: Skip the buy, notify the user immediately ("Your balance is $X — not enough for your $Y weekly DCA. Please deposit funds.").
- **Low balance warning**: After each successful buy, check remaining balance against upcoming DCA schedule and warn proactively (e.g. "You have ~2 weeks of DCA remaining").
- The engine **never** auto-deposits, reduces buy amounts silently, or takes any action on insufficient funds other than notifying the user.

### 4.6 Exchange Support
- **Launch**: Kraken (respected in Bitcoin community, excellent API, supports auto-withdraw to user's own wallet).
- **Future**: Pluggable exchange adapter architecture allows adding support for additional exchanges (e.g. Coinbase Advanced, Binance) and fiat-to-Bitcoin services (e.g. Relai) as their APIs mature.
- Users who prefer not to use any exchange integration can use Notification Mode (§4.2) and buy wherever they choose.

**Important Principle:** The tool will **never** hold user Bitcoin or have withdrawal access. Exchange API keys are stored encrypted (Fernet) and are restricted to trade-only permissions.

## 5. Trust & Security Model

- **No custody**: The tool never holds, controls, or has access to user Bitcoin.
- **No private keys**: Private keys never touch the system.
- **No withdrawal permissions**: Exchange API keys are validated to ensure withdrawal rights are not granted. Keys with withdrawal permissions are rejected.
- **Encrypted API key storage**: All exchange API keys are encrypted at rest using per-user encryption keys.
- **Audit logging**: Every recommendation, execution, skip, retry, and error is logged with a timestamp, the input signals, the rules evaluated, and the outcome. Logs are immutable and user-accessible.
- **User revocation**: Users can revoke exchange API access at any time. Revocation takes effect immediately and disables all pending auto-buy actions.
- **Degraded mode safety**: If data sources are unavailable or stale, the engine reduces confidence and falls back to manual recommendation. It will never execute a buy with insufficient data.

## 6. Performance Comparison & Fee Dashboard

Every user's dashboard shows a **live comparison** of their SteadyStack performance against a naive weekly DCA baseline:

- **Fee efficiency**: Total fees paid as a percentage of volume — the primary measurable edge
- **Average acquisition cost**: SteadyStack vs fixed weekly buy
- **Fee savings**: Absolute and percentage savings from buying during low-fee windows

The baseline is calculated using the same budget and time period, assuming a fixed weekly buy at market price with average mempool fees. This comparison is always visible and cannot be hidden — it's core to the trust model.

### 6.0.1 Backtesting Evidence

Extensive backtesting over 330 weeks (2020–2026) established:

- **Price-timing strategies** (BUY/SKIP/WAIT based on moving averages) **do not reliably beat naive DCA**. In sustained uptrends (most of Bitcoin's history), skipping weeks results in buying later at higher prices.
- **Value averaging / dip-weighted buying** is statistically break-even with naive DCA (±0.3%).
- **Intra-week fee timing** produces real savings: buying on the lowest-fee day within each week saves ~1.2% of invested capital at current fee levels ($100/week DCA).
- **Fee savings scale with rising fees**: As block subsidies halve, on-chain fees will structurally increase, making fee timing increasingly valuable.

These findings inform the product's positioning: SteadyStack optimises for fee efficiency and consistent execution, not price timing.

### 6.0.2 Evidence Dashboard

The Evidence tab presents backtesting findings to users:

- **Strategy comparison chart**: Vertical bar chart showing edge (%) of each timing strategy, with Naive Weekly DCA as a prominent dashed baseline reference line at 0% — clearly demonstrating that price timing fails and fee timing works
- **Strategy detail cards**: For each strategy tested, shows the edge, description, and verdict
- **Intra-week fee variation stats**: 330-week analysis of within-week fee ranges (avg 2.1x, 34% of weeks ≥2x)
- **Halving fee projection table**: Projected fee savings per halving epoch as block subsidy declines
- **Methodology explainer**: Toggleable panel explaining data sources, period, baseline, and fee proxy calculation

### 6.1 What If Projection Tool

A client-side DCA projection tool that lets users visualise how a consistent Bitcoin DCA strategy could grow over time. All computation happens in the browser — no backend API calls required.

**User inputs:**

- Monthly DCA amount (presets: $50–$5,000 + custom)
- Duration (1, 2, 5, 10, or 20 years)
- Fee savings estimate (Conservative ~0.5%, Balanced ~1%, Aggressive ~1.5%)

**Projection model:**

- Three growth scenarios: Bear (~5% CAGR tapering to ~3%), Base (~28% tapering to ~15%), Bull (~50% tapering to ~25%)
- Growth rates taper over long horizons to stay conservative
- SteadyStack advantage modelled as fee savings only — a percentage of each buy that would otherwise be lost to transaction fees. These values are informed by backtesting against 330 weeks of historical data.
- Each scenario shows both SteadyStack-optimised and naive DCA lines

**Visualizations:**

- Area chart with three coloured scenario bands + dashed naive DCA overlay + invested baseline
- Summary cards showing projected USD value (hero), BTC accumulated, ROI %, and extra sats vs naive DCA
- Interactive tooltip with per-scenario breakdown at any point on the timeline

**Safeguards:**

- "Not financial advice" disclaimer with clear caveats about model limitations
- Info panel explaining why bear case shows more BTC than bull (DCA into rising asset dynamics)
- Conservative growth assumptions that taper over time
- Clear labelling that the SteadyStack advantage represents estimated fee savings, not price-timing alpha

**Design rationale:** This tool builds user trust by showing the long-term value of disciplined DCA. The fee-savings overlay is modest and honest — it demonstrates that SteadyStack adds measurable value through fee efficiency without overpromising market-beating returns. It serves as an educational bridge — users explore scenarios for free, then consider automation when they're convinced of the approach. See ADR-012.

## 7. User Feedback & Testimonials

- Users can submit feedback and testimonials from within the dashboard (MVP).
- All submissions require **admin review and approval** before public display.
- Approved testimonials are shown on the public landing page and optionally in marketing materials (post-MVP).
- Feedback includes an optional performance snapshot (anonymised) showing the user's SteadyStack vs naive DCA comparison at time of submission.
- Users can request removal of their published testimonial at any time.

## 8. Pricing Model

Tiers are defined by **features, not volume**. Paid tiers charge a small percentage of DCA volume, which scales naturally with usage and covers hosting costs.

### Free Tier
- Manual fee checking ("are fees low right now?")
- Backtesting evidence dashboard
- What-If DCA projection tool
- Educational content
- No account required, no automation, no notifications

### Automated Tier
- Everything in Free, plus:
- Scheduled fee monitoring + push notifications (Telegram, in-app)
- Notification Mode: fee alerts so user can buy wherever they prefer (§4.2)
- Auto Mode: exchange API buy execution — approval-required or fully automated (§4.3, §4.4)
- Balance monitoring and low-funds alerts (§4.5)
- DCA history tracking and performance dashboard
- **Fee: ~0.3–0.5% of DCA volume**

Fees are collected via **Lightning invoice** at the end of each billing period. The percentage model means revenue scales with usage — users who DCA more contribute proportionally more to hosting costs.

**Design principle:** Cost-covering, not profit-maximising. The goal is sustainable operation, not extraction.

## 9. MVP Features

**Built (v0.2):**
- Fee-aware advisory engine (mempool monitoring, buy/wait recommendation)
- Signal collection pipeline (mempool fees, BTC price, volatility)
- Deterministic scoring with 3 strategy profiles
- Fee Monitor tab — live fee checking with buy/wait advisory
- Evidence tab — backtesting results proving DCA works, fee timing saves money
- Projection tab — What If DCA tool with fee-savings overlay (§6.1)
- Infrastructure tab — Bitcoin sovereignty educational content
- Backtesting module — CLI with policy, accumulation, and fee-timing modes
- Backend test suite passing (run `pytest` to verify)

**Not Yet Built (MVP — completing Free tier):**
- Database integration (models defined, not connected)
- Lightning login (LNURL-auth — account without email/password)
- User feedback submission

**v0.3 — Automated Tier foundations:**
- Scheduled fee monitoring (Celery tasks checking mempool periodically)
- Telegram notifications ("fees are low — good time to buy")
- DCA history tracking and performance dashboard

**v0.4+ — Exchange Automation:**
- Kraken exchange adapter (buy execution + balance checking + auto-withdraw)
- Auto Mode — Approval Required (exchange API execution after user approval)
- Auto Mode — Fully Automated (execution within strict user-defined limits)
- Additional exchange adapters as demand warrants

## 10. Data Sources

- **Mempool fees & congestion**: mempool.space API (with aggressive caching and fallback)
- **Price data & moving averages**: CoinGecko + Binance public API
- **Volatility & momentum**: Calculated internally from price history

Rate limiting is handled with caching and backoff strategies.

## 11. Error Handling & Graceful Degradation

- Stale mempool data → Use last known good data with reduced confidence score
- Telegram unreachable → Log decision and show prominently in dashboard
- Exchange API failure (Auto Mode only, post-MVP) → Fall back to Notification Mode and notify user
- Failed buys are clearly logged with appropriate retry logic where safe
- The engine will never silently fail or make unlogged decisions

## 12. Technical Architecture

**Currently running (local development):**
- **Frontend**: Next.js 16 + React 19 + Tailwind v4 + Recharts 3
- **Backend**: Python 3.12 + FastAPI
- **Decision Engine**: Deterministic rule-based pipeline (signals → policy → decision → explanation)
- **Backtesting**: Custom module using Blockchain.com historical data
- **Caching**: In-memory (backend signal cache with TTLs)
- **External APIs**: mempool.space, CoinGecko, Binance (all free, no keys required)

**Planned (not yet connected):**
- **Hosting**: TBD (no VPS deployed)
- **Deployment**: TBD
- **Database**: PostgreSQL (models defined in code, DB not running)
- **Task Scheduling**: Celery + Redis (docker-compose.dev.yml ready)
- **Exchange Integration**: Pluggable adapter — Kraken first, others as demand warrants

## 13. Success Metrics for MVP

- **Fee efficiency**: Users pay measurably lower transaction fees than fixed-day weekly buys. Backtesting shows ~1–2% fee savings at current levels, increasing with each halving.
- **Consistency**: Users maintain their DCA schedule for ≥90 days without skipping a week. The platform's primary value is keeping users accumulating, especially during bear markets.
- **Educational engagement**: Users interact with the backtesting evidence and report increased confidence in their DCA approach
- **Explanation clarity**: Fee advisory and evidence dashboard are clear and actionable
- **Sustainable cost coverage**: Revenue covers hosting and operational costs