# Architecture Decision Records

This document captures key technical decisions made during the development of SteadyStack, along with the reasoning behind each choice. Decisions are numbered and dated for easy reference.

---

## ADR-001: Python + FastAPI for Backend

**Date:** April 2026  
**Status:** Accepted

**Context:**  
The backend needs to serve a REST API, run scheduled agent logic, and integrate with multiple external APIs (exchanges, mempool.space, CoinGecko). The team considered Node.js (to share language with the frontend) and Python + FastAPI.

**Decision:** Python + FastAPI

**Rationale:**
- FastAPI provides async support, automatic OpenAPI docs, and strong type validation via Pydantic.
- Python has mature libraries for financial data, on-chain analysis, and exchange APIs (ccxt, python-bitcoinlib, etc.).
- The deterministic decision engine is naturally expressed in Python with NumPy/Pandas for signal processing.
- The backend and frontend have distinct concerns; sharing a language adds little value here.

**Trade-offs:**
- Two languages in the stack (TypeScript frontend, Python backend) increases context-switching for solo/small-team development.

---

## ADR-002: LangGraph for Agent Framework

**Date:** April 2026  
**Status:** Superseded by ADR-008

**Context:**  
The buy decision engine needs to evaluate multiple signals, follow branching logic (buy / skip / wait), and produce auditable explanations. Alternatives considered: plain Python state machine, rule engine (e.g., business-rules), or LangGraph.

**Decision:** ~~LangGraph~~ → Superseded. See ADR-008.

**Original Rationale:**
- Natively supports conditional graph-based workflows with explicit "do nothing" paths.
- Built-in state persistence and checkpointing — useful for auditing every decision.
- Integrates cleanly with LLM calls for generating human-readable explanations.

**Why superseded:**  
After analysis, we determined that all financial decisions must be deterministic and reproducible. LLMs add non-determinism, cost, latency, and an external dependency without meaningful benefit over template-based explanations for this use case. LangGraph's strengths (LLM orchestration, graph-based workflows) are unnecessary when every step is a pure deterministic function. A simple Python pipeline is easier to test, audit, and debug. See ADR-008 for the replacement decision.

---

## ADR-003: Next.js for Frontend

**Date:** April 2026  
**Status:** Accepted

**Context:**  
The frontend needs to serve a dashboard showing buy decisions, UTXO health, strategy configuration, and notifications. Considered: Next.js, plain React SPA, SvelteKit.

**Decision:** Next.js

**Rationale:**
- SSR capability useful for SEO on public-facing pages (pricing, landing, educational content).
- Strong ecosystem for auth (NextAuth), API routes for BFF patterns, and deployment flexibility.
- Large community and hiring pool if the team grows.

**Trade-offs:**
- Heavier than a plain SPA for what is primarily an authenticated dashboard.
- App Router adds complexity vs. simpler frameworks.

---

## ADR-004: Celery + Redis for Task Scheduling

**Date:** April 2026  
**Status:** Accepted

**Context:**  
The agent needs to run periodic checks (evaluate buy conditions on a schedule), process background tasks (UTXO monitoring, notification delivery), and handle retries for failed operations. Alternatives: APScheduler, cron + FastAPI background tasks, Celery + Redis.

**Decision:** Celery + Redis

**Rationale:**
- Battle-tested for periodic and async task execution in Python.
- Redis serves double duty as message broker and lightweight cache (for rate-limited API responses).
- Celery beat handles cron-like scheduling natively.
- Retry logic, task chaining, and dead-letter handling are built in.

**Trade-offs:**
- Adds two infrastructure dependencies (Celery workers + Redis) to the Docker Compose stack.
- May be overkill for early MVP with few users — but avoids a migration later.

---

## ADR-005: Lightning Login as Primary Auth

**Date:** April 2026  
**Status:** Accepted

**Context:**  
The target audience is Bitcoiners who value privacy and self-sovereignty. Standard email/password auth is familiar but requires storing PII. Alternatives: email + passkey, Nostr login (NIP-07), Lightning login (LNURL-auth).

**Decision:** Lightning login (preferred), with email + passkey as fallback

**Rationale:**
- LNURL-auth requires no PII — aligns perfectly with the self-custody ethos.
- Users already have Lightning wallets if they're doing Bitcoin DCA.
- Cryptographic proof of identity without passwords or email verification.
- Email + passkey fallback ensures accessibility for users without Lightning wallets.

**Trade-offs:**
- Smaller adoption base than email auth — mitigated by offering both options.
- LNURL-auth libraries are less mature than traditional auth solutions.

---

## ADR-006: Pluggable Exchange Abstraction Layer

**Date:** April 2026  
**Status:** Accepted

**Context:**  
Auto Mode requires placing trades on user-connected exchanges. Each exchange has a different API. Considered: direct per-exchange integrations, ccxt library, or custom abstraction layer.

**Decision:** Custom pluggable abstraction layer (potentially built on top of ccxt)

**Rationale:**
- Decouples exchange-specific logic from the agent's decision engine.
- New exchanges can be added as plugins without touching core logic.
- Allows enforcing permission constraints (read + trade only) at the abstraction level.
- ccxt can be used internally but wrapped to enforce our security and permission model.

**Trade-offs:**
- Upfront design cost for the abstraction interface.
- Must be maintained as exchange APIs evolve.

---

## ADR-007: PostgreSQL for Primary Database

**Date:** April 2026  
**Status:** Accepted

**Context:**  
Need to store user profiles, strategy configurations, decision logs, UTXO snapshots, and historical price data. Considered: PostgreSQL, SQLite, MongoDB.

**Decision:** PostgreSQL

**Rationale:**
- Strong relational model suits the structured data (users → strategies → decisions → logs).
- JSONB columns available for semi-structured data (agent reasoning, API responses).
- Excellent tooling, extensions (TimescaleDB if time-series needs grow), and Docker support.
- Proven at scale if user base grows.

**Trade-offs:**
- Heavier than SQLite for early development — but SQLite doesn't support concurrent writes well, which matters with Celery workers.

---

## ADR-008: Deterministic Decision Engine (No LLM in Decision Path)

**Date:** April 2026  
**Status:** Accepted (supersedes ADR-002)

**Context:**  
The buy decision engine needs to evaluate market signals and decide whether to buy, skip, or wait. The original plan used LangGraph with LLM integration for both decision-making and explanation generation. After review, we reconsidered whether LLM involvement in the decision path is appropriate for a financial tool.

**Decision:** Fully deterministic, rule-based decision pipeline with template-based explanations. No LLM in the decision or explanation path for MVP.

**Rationale:**
- **Reproducibility**: Given the same inputs, the engine must always produce the same output. This is essential for trust, auditing, and backtesting. LLMs are inherently non-deterministic.
- **Auditability**: Every decision can be traced to specific rules and thresholds. Users and regulators can verify exactly why a buy or skip occurred.
- **No external dependency in the critical path**: The decision loop has zero reliance on third-party AI inference APIs. No latency, no cost-per-decision, no downtime risk from an LLM provider.
- **Template explanations are better for this use case**: Showing exact numbers, thresholds, and rule outcomes is more trustworthy than a conversational LLM summary for financial decisions.
- **Simplicity**: A Python function pipeline (signals → policy → decision → explanation) is easier to test, debug, and reason about than a graph-based agent framework.

**Architecture:**
```
collect_signals()  →  evaluate_policy()  →  make_decision()  →  format_explanation()
   (mempool,           (deterministic        (buy/skip/wait     (template with
    price, vol)         scoring + rules)       + amount)          exact inputs)
```

**Trade-offs:**
- Explanations are less conversational than LLM-generated text. Mitigated by well-designed templates.
- Cannot handle truly novel market situations that rules don't cover. Mitigated by conservative defaults (skip when uncertain).

**Revisit if:** Post-MVP, LLMs may be introduced for optional features like personalised insights, natural-language strategy configuration, or educational content — but never in the financial decision path.

---

## ADR-009: No-Custody / No-Withdrawal Architecture

**Date:** April 2026  
**Status:** Accepted

**Context:**  
A Bitcoin DCA tool that interacts with exchanges and wallets could technically be designed to hold funds in escrow or use omnibus wallets. We needed to decide the custody model.

**Decision:** Strict no-custody, no-withdrawal architecture. The system never holds, controls, or has the ability to move user Bitcoin.

**Rationale:**
- **Regulatory**: Holding user funds triggers money transmitter and custodial regulations in most jurisdictions. Avoiding custody eliminates this entire category of compliance burden.
- **Security**: No custody means a system breach cannot result in loss of user funds. The attack surface for financial loss is zero.
- **Trust**: Self-custody is a core value of the target audience. Any custodial element would undermine product-market fit.
- **Implementation**: Watch-only wallets (xpub/descriptor import) allow full monitoring without signing capability. Exchange API keys are validated to reject withdrawal permissions. PSBT support allows transaction preparation without signing.

**Enforcement:**
- Exchange API key validation rejects keys with withdrawal permissions at connection time.
- No signing keys or seed phrases are ever stored or transmitted.
- Audit logs record every API call made to exchanges, with full request/response logging.

**Trade-offs:**
- Users must act on recommendations independently in Advisory Mode, adding friction. Mitigated by clear notification workflow.
- Auto Mode is limited to exchange-side execution (no on-chain sends). This is acceptable for the use case.

---

## ADR-010: Advisory Mode as Default Operating Model

**Date:** April 2026  
**Status:** Accepted

**Context:**  
The system supports two operating models: Advisory Mode (recommendations only — the user acts independently) and Auto Mode (the app places buys via exchange API). We needed to decide which is the default and which ships first.

**Decision:** Advisory Mode is the default and the only mode in MVP. Auto Mode is post-MVP.

**Mode definitions:**
- **Advisory Mode** (MVP): The engine recommends buy opportunities and notifies the user with full reasoning. The user decides whether to act and places the buy themselves. The app does not execute any trades.
- **Auto Mode — Approval Required** (post-MVP, Pro): The engine sends a recommendation and waits for explicit user approval before placing the buy on the connected exchange.
- **Auto Mode — Notifications Only** (post-MVP, Pro): The engine places buys automatically within strict user-defined limits and immediately notifies the user with reasoning and execution details.

**Rationale:**
- **Lower risk**: Advisory Mode cannot execute any action. This eliminates an entire class of bugs (accidental buys, wrong amounts, exchange errors).
- **Faster to ship**: No exchange API integration needed for MVP — the engine just needs to recommend and explain.
- **Honest naming**: "Advisory" accurately describes what the app does in this mode. It advises; the user acts. Previous naming ("Managed Mode") implied the app was managing execution, which was misleading.
- **Trust building**: Users learn to trust the engine's recommendations before granting it any execution capability.
- **Simpler compliance**: No automated trading means fewer regulatory considerations for launch.

**Trade-offs:**
- Higher friction for users who want hands-off DCA. Mitigated by making the notification workflow as smooth as possible and by the performance comparison dashboard showing clear evidence of better outcomes.
- Some users may not see value in a recommendation-only tool. Mitigated by the two Auto Mode tiers available post-MVP, offering a clear upgrade path.

---

## ADR-011: Market Data Source and Fallback Strategy

**Date:** April 2026  
**Status:** Accepted

**Context:**  
The decision engine relies on external market data (mempool fees, BTC price, on-chain metrics). These sources can be rate-limited, temporarily unavailable, or return stale data. We needed a strategy for source selection and degraded operation.

**Decision:** Use free public APIs with aggressive caching, multiple fallback sources, and a confidence-scoring system that degrades gracefully.

**Primary sources:**
- **Mempool fees**: mempool.space API (public endpoint, cached aggressively)
- **Price data**: CoinGecko free API → Binance public API (fallback)
- **On-chain metrics**: mempool.space → optional self-hosted Electrum server (fallback)
- **Volatility/momentum**: Calculated internally from cached price history

**Fallback strategy:**
1. Each data source has a primary and at least one fallback.
2. All responses are cached in Redis with appropriate TTLs (fees: 1-2 min, price: 1 min, on-chain: 5 min).
3. If all sources for a signal are unavailable, the engine uses the last known good value but reduces the overall confidence score.
4. If the confidence score falls below a configurable threshold, the engine skips the buy window and notifies the user explaining why.
5. The engine never executes a buy with stale or missing data without user override.

**Rationale:**
- Free APIs keep operational costs near zero for MVP.
- Caching reduces API calls and insulates against rate limits and brief outages.
- Confidence scoring makes degradation visible and auditable rather than silent.
- Conservative default (skip when uncertain) protects users.

**Trade-offs:**
- Free API tiers have lower rate limits. Mitigated by aggressive caching and the fact that buy decisions happen at most a few times per day, not per second.
- CoinGecko free tier is limited to ~30 calls/min. At MVP scale this is sufficient; may need paid tier or additional sources as user count grows.

**Revisit if:** User count exceeds free API tier limits, or if a data source becomes unreliable.

---

## ADR-012: Client-Side What If Projection Tool

**Date:** April 2026  
**Status:** Accepted

**Context:**  
To build user trust and demonstrate the value of disciplined DCA (and SteadyStack's timing edge), we wanted a forward-looking projection tool. The question was whether this should be a backend API (using historical backtesting data) or a client-side computation.

**Decision:** Client-side projection model running entirely in the browser, with no backend API calls.

**Rationale:**
- **Zero latency**: Projections update instantly as users adjust inputs (amount, duration, strategy). No API round-trips means a fluid, exploratory experience.
- **No backend cost**: Projection is pure math — growth curves, DCA accumulation, and SS edge calculation. There's no data to fetch that isn't already parameterised.
- **Privacy**: Users' financial exploration (how much they plan to invest) never leaves their browser.
- **Simplicity**: One TypeScript file (`projection.ts`) with a single pure function. Easy to test and reason about.
- **Offline-capable**: The projection tool works even if the backend is temporarily unavailable.

**Model design:**
- Three growth scenarios (bear/base/bull) with annualised CAGR that tapers over long horizons to stay conservative.
- SteadyStack edge is parameterised by strategy profile: Conservative (~2%), Balanced (~4%), Aggressive (~6%), informed by the comparison module's backtested results.
- Both naive DCA and SteadyStack lines are shown for each scenario, making the edge visible as a widening gap.

**Trade-offs:**
- The model uses simplified growth curves, not actual historical replay. This is intentional — the tool is educational, not predictive.
- Growth rate assumptions may need periodic review as Bitcoin's market matures.
- Disclaimer and info panels are essential to prevent users from treating projections as financial advice.

**Revisit if:** Users request historical backtesting-based projections, or if we need to incorporate real fee data into the projection model.

---

## ADR-013: Single-Page Dashboard for MVP

**Date:** April 2026  
**Status:** Accepted

**Context:**  
The original project structure (`project-structure.md`) envisioned a multi-route dashboard with separate pages for decisions, comparison, strategy management, UTXO health, history, and settings. For MVP, we needed to decide whether to build the full routing structure or consolidate into a simpler layout.

**Decision:** Single-page dashboard for MVP, with all three core sections (Market Analysis, Performance Comparison, What If Projection) rendered on one page.

**Rationale:**
- **Faster to ship**: One page with three sections is dramatically simpler than six+ routes with shared state management.
- **Better UX for MVP scope**: With only three features, a single scrollable page gives users a complete picture without navigation friction. Users can see their decision, comparison, and projection without clicking around.
- **Progressive disclosure**: Each section can be expanded or collapsed independently. The What If panel only renders its chart after client-side hydration.
- **Easy to split later**: Each section is a self-contained component (`DecisionPanel`, `ComparisonPanel`, `WhatIfPanel`). Migrating to separate routes post-MVP requires only routing changes, not component rewrites.

**Trade-offs:**
- Page can become long as features grow. Mitigated by clean section separators and potential tab/accordion patterns post-MVP.
- All sections load together, increasing initial bundle size. Mitigated by dynamic imports for chart-heavy components.
- Not suitable once auth, settings, and admin pages are needed — but those are post-MVP concerns.

**Revisit if:** MVP grows beyond 3-4 dashboard sections, or when auth and settings pages are implemented.

---

## ADR-014: Next.js API Proxy Routes (BFF Pattern)

**Date:** April 2026  
**Status:** Accepted

**Context:**  
The frontend needs to communicate with the FastAPI backend. Options considered: direct browser-to-backend calls (CORS), Next.js rewrites proxy, or Next.js API route handlers acting as a Backend-for-Frontend (BFF) proxy.

**Decision:** Next.js API route handlers that proxy requests to the backend.

**Rationale:**
- **Works through any proxy**: Unlike Next.js rewrites (which can break behind reverse proxies or preview environments), API route handlers make server-side fetch calls that always resolve correctly.
- **Single origin**: The browser only talks to the Next.js server. No CORS configuration needed.
- **Error handling**: Each proxy route can catch backend errors and return clean JSON responses to the frontend.
- **Future flexibility**: API routes can add authentication checks, rate limiting, or request transformation without touching the frontend components or the backend.

**Implementation:**
- `src/app/api/decisions/run/route.ts` → POST to backend `/api/decisions/run`
- `src/app/api/decisions/profiles/route.ts` → GET to backend `/api/decisions/profiles`
- `src/app/api/comparison/simulate/route.ts` → POST to backend `/api/comparison/simulate`
- `src/app/api/health/route.ts` → GET to backend `/health`

**Trade-offs:**
- Adds a small amount of latency (extra hop through Next.js server). Negligible for the request frequency of this app.
- Each new backend endpoint needs a corresponding proxy route. Mitigated by the small number of endpoints in MVP.

**Revisit if:** The number of backend endpoints grows significantly, at which point a generic proxy middleware may be more maintainable than individual route files.

---

## ADR-014: Product Pivot — Fee-Aware DCA Platform (Not Smart Timing)

**Date:** April 2026  
**Status:** Accepted

**Context:**  
The original SteadyStack value proposition was a "smart DCA agent" that would achieve 2–6% cost-basis improvement over naive weekly DCA through intelligent BUY/SKIP/WAIT decisions based on mempool fees, price vs moving averages, and volatility signals.

A comprehensive backtesting module was built to validate these claims against 330 weeks of historical data (2020–2026). Three approaches were tested:

1. **Policy engine (BUY/SKIP/WAIT):** Skipping weeks based on price/fee/volatility signals. Result: -8% to -58% cost edge — actively harmful. In Bitcoin's predominantly uptrending market, skipping weeks means buying later at higher prices.

2. **Value averaging / dip-weighted buying:** Always buy, but vary amount based on price position vs 30d moving average. Result: ±0.3% — statistically break-even with naive DCA.

3. **Intra-week fee timing:** Buy on the lowest-fee day within each week instead of a fixed day. Result: ~1.2% fee savings at current fee levels ($100/week). However, price variation within the week (~2–3%) largely offsets the fee savings in BTC terms.

The conclusion is unambiguous: **no mechanical timing strategy reliably beats naive weekly DCA on cost basis over multi-year periods.**

**Decision:** Pivot the product from "smart timing agent" to "self-sovereign Bitcoin accumulation platform" with five pillars:

1. **Automation without custody** — consistent DCA execution, no key custody
2. **Fee-aware buying** — mempool monitoring to minimise transaction fees
3. **Best-practice education** — historical data showing why DCA works and timing doesn't
4. **Node/DATUM infrastructure** — self-sovereign infrastructure for advanced users
5. **Honest positioning** — transparency about what works and what doesn't

The SS_EDGE values in the projection tool are reduced from 2/4/6% (unvalidated price-timing claims) to 0.5/1/1.5% (fee savings only, backed by data).

**Rationale:**
- Honesty is a commercial advantage in a space full of "AI trading" hype
- Fee savings are real, measurable, and will increase over time as block subsidies halve
- The behavioural value (keeping users DCA-ing through bear markets) is worth more than any timing edge
- The target audience (non-technical Bitcoin accumulators who won't run their own node) benefits most from automation and education, not alpha generation
- The product becomes more trustworthy and more distinctive than before

**Trade-offs:**
- The "smart timing" narrative was more exciting for marketing. The honest narrative requires users who value substance over hype.
- Fee savings are modest today (~1–2%). The value proposition strengthens with each halving but requires patience.
- Some already-built engine features (price scoring, volatility scoring, skip logic) become less central. They remain useful for educational display and market context, but are no longer the primary value driver.

**Revisit if:** On-chain fee dynamics change dramatically (e.g., widespread Lightning adoption makes on-chain fees irrelevant for DCA), or new research demonstrates a reliable, backtestable timing edge.

---

## Template for Future Decisions

```
## ADR-NNN: [Title]

**Date:** [Date]  
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-NNN

**Context:** [What problem or question prompted this decision?]

**Decision:** [What was decided]

**Rationale:** [Why this option was chosen]

**Trade-offs:** [What are the downsides or risks?]

**Revisit if:** [Under what conditions should this be reconsidered?]
```
