# SteadyStack

SteadyStack automates Bitcoin accumulation in the simplest proven way — regular DCA — while reducing fee drag, preserving self-custody, and supporting advanced users with their own node, DATUM gateway, and template infrastructure.

We don't promise to beat Bitcoin with clever timing. We show, using historical data, why disciplined DCA is usually best — then help users implement it properly.

**Status:** Active Development (MVP in progress)

---

## How It Works

1. Connect a **watch-only wallet** (Sparrow, Electrum, hardware wallet, etc.).
2. Set your monthly budget and preferred payout address.
3. The engine monitors mempool conditions and recommends **when fees are low** to execute your weekly buy.
4. You decide whether to act. The app never places a buy for you in Advisory Mode.
5. Track your **fee savings and accumulation** on your dashboard.

## Why SteadyStack?

We backtested 330 weeks of historical data (2020–2026). The honest conclusion:

- **Price timing doesn't work.** No mechanical strategy reliably beats naive weekly DCA on cost basis.
- **Fee timing does work.** Buying on the lowest-fee day within each week saves ~1–2% of invested capital.
- **Fees will rise.** As Bitcoin's block subsidy halves, on-chain fees must increase. Fee-aware buying becomes more valuable every cycle.
- **Consistency is the real edge.** Most people stop DCA during bear markets. The biggest win is simply keeping you accumulating.

## Operating Modes

| Mode | Who executes? | MVP? |
|---|---|---|
| **Advisory Mode** | You — the app recommends, you act independently | Yes |
| **Auto Mode — Approval Required** | App, after your explicit approval | Post-MVP (Pro) |
| **Auto Mode — Notifications Only** | App, automatically within your limits | Post-MVP (Pro) |

## Current Features (What's Built)

- **Fee Monitor** — live mempool fee checking with buy/wait advisory based on current congestion
- **Evidence Dashboard** — backtesting results from 330 weeks of data, proving DCA works and fee timing saves money
- **DCA Projection Tool** — client-side projections across bear/base/bull scenarios with honest fee-savings overlay (0.5–1.5%)
- **Infrastructure Guide** — educational content on Bitcoin Knots, DATUM gateway, and BIP 110
- **Backtesting Engine** — CLI module with three modes: policy engine, accumulation, and intra-week fee timing

## Core Principles

- **Honesty over hype** — we tested the data, simple DCA wins, fee savings are the real edge
- **No custody, no keys** — the app never holds funds, stores private keys, or has withdrawal permissions
- **Full auditability** — every recommendation and outcome is logged with exact inputs and rules
- **Transparency by default** — your performance vs a standard DCA baseline is always visible

## Tech Stack

| Layer | Technology | Status |
|---|---|---|
| **Backend** | Python 3.12 + FastAPI | Running |
| **Frontend** | Next.js 16 + React 19 + Tailwind v4 | Running |
| **Charts** | Recharts 3 | Running |
| **Decision Engine** | Deterministic pipeline: signals → policy → decision → explanation | Running |
| **Backtesting** | Custom module with Blockchain.com historical data | Running |
| **Database** | PostgreSQL (models defined, DB not connected) | Planned |
| **Task Queue** | Celery + Redis | Planned |
| **Bitcoin** | Electrum RPC (watch-only) + PSBT | Planned |
| **Deployment** | Local only — no VPS or cloud | Planned |

## Project Structure

```
BTCDCA/
├── docs/                  # Specification, ADRs, project structure
├── backend/               # Python + FastAPI backend
│   └── app/
│       ├── signals/       # ✓ Market data collection (mempool, price, volatility)
│       ├── policy/        # ✓ Deterministic rules and scoring
│       ├── engine/        # ✓ Decision pipeline orchestration
│       ├── comparison/    # ✓ Performance vs naive DCA baseline
│       ├── backtest/      # ✓ Historical backtesting (policy, accumulation, fees)
│       ├── models/        # ✓ Database models (defined, not connected)
│       └── api/           # ✓ REST API routes
├── frontend/              # Next.js frontend
│   └── src/
│       ├── components/    # ✓ FeeMonitor, Evidence, WhatIf, Infrastructure panels
│       ├── lib/           # ✓ API client, projection model
│       └── app/           # ✓ 4-tab dashboard + API proxy routes
└── docker-compose.dev.yml # Local dev services (Postgres, Redis)
```

See [`docs/project-structure.md`](docs/project-structure.md) for the full layout.

## Documentation

- [**Specification**](docs/specification.md) — product vision, modes, trust model, MVP scope, success metrics
- [**Architecture Decisions**](docs/architecture-decisions.md) — ADR log with rationale for all key technical choices
- [**Project Structure**](docs/project-structure.md) — directory layout, module responsibilities, architectural boundaries

## Pricing

| Tier | Volume | Cost |
|---|---|---|
| **Free** | Up to $500/month | Free |
| **Pro** | Unlimited | 0.5% of monthly volume, capped at $25/month |

Fees collected via Lightning invoice.

## Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- Git

### Backend

```bash
git clone https://github.com/zartyblartfast/SteadyStack.git
cd SteadyStack/backend
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest
```

### Frontend

```bash
cd SteadyStack/frontend
npm install

# Development server (backend must be running on port 8000)
npx next dev -p 3002

# Production build
npm run build
```

### Full Stack (Docker — coming soon)

```bash
cp .env.example .env
docker compose up
```

## License

TBD
