# Project Structure

Directory layout for SteadyStack. Items marked ✓ are implemented; † marks stale/unused code pending cleanup; unmarked items are planned.

Last updated: April 2026 (spec v1.0, post-pivot — see ADR-014).

The core design principle is **separation of concerns**: signal collection, policy rules, decision execution, and explanation generation are independent modules. Business logic never leaks into orchestration or API layers.

---

```
BTCDCA/
├── docs/                          # Project documentation
│   ├── specification.md           # ✓ Product specification (v1.0)
│   ├── architecture-decisions.md  # ✓ ADR log (ADR-001 through ADR-014)
│   ├── project-structure.md       # ✓ This file
│   ├── coding-standards.md        # ✓ Code style and conventions
│   └── testing-strategy.md        # ✓ Test approach and coverage goals
│
├── backend/                       # Python + FastAPI backend
│   ├── app/
│   │   ├── main.py                # ✓ FastAPI application entry point
│   │   ├── config.py              # ✓ Environment config and settings
│   │   ├── schemas.py             # ✓ Pydantic request/response schemas
│   │   │
│   │   ├── api/                   # ✓ REST API routes
│   │   │   ├── decisions.py       # ✓ POST /api/decisions/run, GET /api/decisions/profiles
│   │   │   ├── comparison.py      # † POST /api/comparison/simulate (old, unused by frontend)
│   │   │   └── health.py          # ✓ GET /health
│   │   │
│   │   ├── signals/               # ✓ Signal collection (Spec §11)
│   │   │   ├── mempool.py         # ✓ mempool.space API client — fees & congestion
│   │   │   ├── price.py           # ✓ CoinGecko + Binance — price & moving averages
│   │   │   ├── volatility.py      # ✓ Volatility & momentum — calculated from price history
│   │   │   ├── cache.py           # ✓ In-memory caching with TTLs and fallback
│   │   │   ├── collector.py       # ✓ Orchestrates all signal fetches into a SignalSnapshot
│   │   │   └── exceptions.py      # ✓ Signal-specific exception types
│   │   │
│   │   ├── policy/                # ✓ Deterministic rules & scoring (Spec §2, ADR-008)
│   │   │   ├── profiles.py        # ✓ Strategy profile definitions (conservative, balanced, aggressive)
│   │   │   ├── evaluator.py       # ✓ Buy/skip/wait evaluation logic
│   │   │   └── scoring.py         # ✓ Weighted signal scoring per profile
│   │   │
│   │   ├── engine/                # ✓ Decision pipeline orchestration (ADR-008)
│   │   │   ├── pipeline.py        # ✓ signals → policy → decision → explanation
│   │   │   └── explain.py         # ✓ Template-based explanation generator
│   │   │
│   │   ├── comparison/            # ✓ Performance comparison (Spec §6)
│   │   │   ├── baseline.py        # ✓ Naive weekly DCA baseline calculator
│   │   │   ├── tracker.py         # ✓ Tracks SteadyStack vs naive performance
│   │   │   └── metrics.py         # ✓ Cost improvement, fee efficiency metrics
│   │   │
│   │   ├── backtest/              # ✓ Historical backtesting module (ADR-014)
│   │   │   ├── __main__.py        # ✓ CLI entry point (python -m app.backtest)
│   │   │   ├── data.py            # ✓ Blockchain.com API data fetcher with caching
│   │   │   ├── runner.py          # ✓ Policy engine + accumulation backtest runners
│   │   │   ├── accumulation.py    # ✓ Dip-weighted accumulation engine
│   │   │   ├── fee_timing.py      # ✓ Intra-week fee timing analysis
│   │   │   ├── snapshot_builder.py # ✓ Builds SignalSnapshots from historical data
│   │   │   ├── report.py          # ✓ Formatted report output for all modes
│   │   │   └── cache/             # ✓ Cached historical data (JSON)
│   │   │
│   │   └── models/                # ✓ Database models (defined but DB not connected)
│   │       ├── database.py        # ✓ Database connection setup
│   │       ├── user.py            # ✓ User model
│   │       ├── strategy.py        # ✓ Strategy profile model
│   │       └── decision.py        # ✓ Decision log model
│   │
│   ├── tests/                     # ✓ Backend test suite (68 tests passing)
│   │   ├── test_signals/          # ✓ Signal collection tests (mempool, price, volatility)
│   │   ├── test_engine.py         # ✓ Pipeline integration tests
│   │   ├── test_comparison.py     # ✓ Baseline and metrics tests
│   │   ├── test_backtest.py       # ✓ Backtest module tests
│   │   ├── test_golden.py         # ✓ Golden file tests for deterministic decisions
│   │   ├── test_invariants.py     # ✓ Property-based invariant tests
│   │   ├── test_api.py            # ✓ API endpoint tests
│   │   └── golden/                # ✓ Golden test fixtures (YAML)
│   │
│   └── requirements.txt           # ✓ Python dependencies
│
├── frontend/                      # Next.js 16 + React 19 frontend
│   ├── src/
│   │   ├── app/                   # ✓ Next.js App Router
│   │   │   ├── page.tsx           # ✓ 4-tab dashboard: Fees, Evidence, Projection, Infrastructure
│   │   │   ├── layout.tsx         # ✓ Root layout with dark theme
│   │   │   ├── globals.css        # ✓ Tailwind v4 dark theme with CSS variables
│   │   │   └── api/               # ✓ Next.js API proxy routes (BFF pattern, ADR-013)
│   │   │       ├── decisions/
│   │   │       │   ├── run/route.ts       # ✓ POST → backend /api/decisions/run
│   │   │       │   └── profiles/route.ts  # ✓ GET → backend /api/decisions/profiles
│   │   │       └── health/route.ts        # ✓ GET → backend /health
│   │   │
│   │   ├── components/            # UI components
│   │   │   ├── Header.tsx             # ✓ App header — "Fee-Aware · Non-Custodial" badge
│   │   │   ├── FeeMonitorPanel.tsx    # ✓ Live mempool fees, buy/wait advisory, tips
│   │   │   ├── EvidencePanel.tsx      # ✓ Backtesting results, strategy chart, halving table
│   │   │   ├── WhatIfPanel.tsx        # ✓ DCA projection (3 scenarios, fee-savings overlay)
│   │   │   └── InfrastructurePanel.tsx # ✓ Knots/DATUM/BIP 110 education
│   │   │
│   │   └── lib/                   # ✓ Utility functions
│   │       ├── api.ts             # ✓ Typed API client (decisions, comparison, health)
│   │       └── projection.ts      # ✓ Client-side DCA projection model (fee-savings edge)
│   │
│   ├── public/                    # Static assets
│   ├── package.json               # ✓ Dependencies (Next.js 16, React 19, Recharts 3, Lucide)
│   └── next.config.ts             # ✓ Next.js configuration
│
├── docker-compose.dev.yml         # ✓ Local dev services (Postgres, Redis) — not yet used by app
├── .env.example                   # ✓ Environment variable template
├── .gitignore                     # ✓
└── README.md                      # ✓ Product overview and dev instructions
```

---

## Module Responsibility Map

### Implemented

| Module | Spec Section | Responsibility |
|---|---|---|
| `backend/app/signals/` | §11 | Collects live market data (mempool fees, price, volatility) with caching |
| `backend/app/policy/` | §2, ADR-008 | Deterministic scoring and profile evaluation |
| `backend/app/engine/` | ADR-008 | Orchestrates the pipeline: signals → policy → decision → explanation |
| `backend/app/comparison/` | §6 | Performance comparison logic (naive DCA baseline, metrics) |
| `backend/app/backtest/` | ADR-014 | Historical backtesting: policy, accumulation, and fee-timing modes |
| `backend/app/api/` | — | REST endpoints: decisions, comparison, health |
| `frontend/src/app/page.tsx` | §6 | 4-tab dashboard: Fees, Evidence, Projection, Infrastructure |
| `frontend/src/components/FeeMonitorPanel.tsx` | §6 | Live fee advisory using backend signal data |
| `frontend/src/components/EvidencePanel.tsx` | §6.0.1 | Backtesting evidence with charts and halving projections |
| `frontend/src/components/WhatIfPanel.tsx` | §6.1 | Client-side DCA projection with fee-savings overlay |
| `frontend/src/components/InfrastructurePanel.tsx` | §8 | Knots, DATUM, BIP 110 educational content |
| `frontend/src/lib/projection.ts` | §6.1 | Growth model with fee-savings edge (0.5/1/1.5%) |
| `frontend/src/app/api/` | ADR-013 | Next.js proxy routes forwarding to backend |

### Planned (Not Yet Built)

| Module | Spec Section | Responsibility |
|---|---|---|
| `backend/app/exchanges/` | §4.2, §4.3 | Exchange API abstraction for automated buys |
| `backend/app/bitcoin/` | §4.1, §5 | Watch-only wallet, UTXO analysis, PSBT |
| `backend/app/notifications/` | §10 | Telegram + in-app notification delivery |
| `backend/app/tasks/` | §13 | Celery scheduled DCA evaluation and background tasks |
| `backend/app/auth/` | §10 | Lightning login + passkey authentication |
| `frontend/src/app/dashboard/` | §3 | Multi-page user dashboard |
| `frontend/src/app/login/` | §10 | Authentication pages |
| `frontend/src/app/admin/` | §7 | Admin feedback review interface |

---

## Key Architectural Boundaries

The decision engine is structured as a **pure function pipeline** (see ADR-008):

```
signals/collector.py  →  policy/scoring.py  →  engine/pipeline.py  →  engine/explain.py
    (fetch data)          (apply rules)         (buy/skip/wait)       (template output)
```

- **signals/** has no knowledge of policy rules or decisions. It only fetches and caches data.
- **policy/** has no knowledge of where signals came from or how decisions are delivered. It only scores and evaluates rules.
- **engine/** orchestrates the pipeline and produces a Decision object. It does not contain business logic.
- **explain.py** formats the Decision into a human-readable template. No LLM calls.

This separation ensures the deterministic policy logic is independently testable and auditable.

The **frontend** communicates with the backend exclusively through Next.js API proxy routes (BFF pattern, ADR-013). The browser never calls the backend directly.

---

## External Services

All currently used services are free, no-API-key-required public APIs:

| Service | Used By | Purpose |
|---|---|---|
| mempool.space | `signals/mempool.py` | Live mempool depth, fee rates |
| CoinGecko | `signals/price.py` | BTC price, moving averages (free tier) |
| Binance | `signals/price.py` | BTC price (public market data) |
| Blockchain.com | `backtest/data.py` | Historical daily data for backtesting |

---

## Conventions

- **Backend**: Python 3.12+, type hints everywhere, Pydantic for validation, async where beneficial.
- **Frontend**: TypeScript strict mode, Tailwind CSS v4 for styling, Recharts for charts, Lucide for icons.
- **Testing**: pytest for backend (68 tests). Policy and scoring tests are highest priority.
- **Environment**: All secrets via environment variables, never committed. See `.env.example`.
- **Running locally**: Both servers required — backend on port 8000, frontend on port 3002.
