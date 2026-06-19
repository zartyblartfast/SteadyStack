# SteadyStack Session Handoff — 2026-06-18

Use this file to resume campaign-platform work in a fresh Hermes session without carrying the full previous chat context.

## Repo / branch

- Repo path on VPS: `/tmp/SteadyStack-inspect`
- GitHub repo: `https://github.com/zartyblartfast/SteadyStack`
- Branch: `feature/campaign-platform`
- Latest pushed commit at handoff: `37028b7 refactor: remove direct Bitcoin metric collectors`

## Important instruction for the next agent

Before editing, read the DOX files that apply to the work area:

- `AGENTS.md`
- `backend/AGENTS.md` for backend work
- `backend/app/signals/AGENTS.md` for Bitcoin Card / metrics work
- `backend/app/campaigns/AGENTS.md` for campaign-domain work
- `frontend/AGENTS.md` for UI work
- `docs/AGENTS.md` for docs/spec work

Also read the v0.3 source-of-truth spec:

- `docs/specs/campaign-platform-v0.3.md`

## Current product direction

SteadyStack is evolving from a fee-aware Bitcoin DCA prototype into a campaign-based Bitcoin accumulation platform.

Core principles:

- Bitcoin Card is the only normal-path Bitcoin metrics/data provider.
- If SteadyStack needs a Bitcoin metric that Bitcoin Card does not expose, enhance Bitcoin Card first rather than adding a direct source to SteadyStack.
- BMRI and Bitcoin Risk are valuation context, not automated trading signals.
- BMRI remains the default Bear Market Boost trigger for now.
- Bitcoin Risk is shown as separate valuation-risk context; do not blend it into an opaque composite with BMRI yet.
- Fee optimisation is default for campaigns.
- Fee displays should lead with fee as % of buy, then estimated USD fee, then sat/vB.
- Advisory-first; automation is later only with restricted trade-only exchange API keys and withdrawals disabled/rejected.
- No custody, no seed phrases, no withdrawal-enabled credentials.

## Completed docs/design work

Committed docs/sketch artifacts include:

- `docs/campaign-platform-evolution.md`
- `docs/specs/campaign-platform-v0.3.md`
- `docs/specs/bitcoin-card-fee-history-enhancements.md`
- `docs/ui-sketches/campaign-ui-v2/`
- `docs/ui-sketches/campaign-ui-v3/`
- DOX files:
  - `AGENTS.md`
  - `backend/AGENTS.md`
  - `backend/app/campaigns/AGENTS.md`
  - `backend/app/signals/AGENTS.md`
  - `frontend/AGENTS.md`
  - `docs/AGENTS.md`

## Completed backend work

Bitcoin Card adapter:

- File: `backend/app/signals/bitcoin_card.py`
- Supports:
  - `/api/summary`
  - `/api/fee-history`
  - `/api/fee-profile`
  - `/api/bmri-comparison`
  - `/api/bitcoin-risk`

SteadyStack API endpoints:

- `GET /api/metrics/summary`
- `GET /api/metrics/bmri`
- `GET /api/metrics/bitcoin-risk`
- `GET /api/fees/history/{period}`
- `GET /api/fees/profile?cadence=weekly&buyAmountUsd=100&targetVbytes=140`

Campaign-domain foundation:

- `backend/app/campaigns/schemas.py`
- `backend/app/campaigns/state.py`
- `backend/app/campaigns/events.py`
- `backend/app/campaigns/repository.py`

Signal collector:

- `backend/app/signals/collector.py` now uses Bitcoin Card summary/BMRI history for normal live decision inputs.
- Direct normal-path collectors were removed:
  - deleted `backend/app/signals/price.py`
  - deleted `backend/app/signals/mempool.py`
  - deleted corresponding direct-source tests

Configuration cleanup:

- `backend/app/config.py` no longer has CoinGecko/Binance/mempool API URLs.
- `.env.example` only exposes `BITCOIN_CARD_BASE_URL` for Bitcoin market metrics.

## Completed frontend work

Valuation UI:

- File: `frontend/src/components/ValuationContextPanel.tsx`
- Added new app tab: `Valuation`
- Shows:
  - BTC price
  - BMRI
  - Bitcoin Risk
  - stacked charts for Price / BMRI / Bitcoin Risk
  - source/caveat/fetched timestamps
- Time range controls:
  - `1M`
  - `6M`
  - `1Y`
  - `2Y`
  - `5Y`
  - `All`
- Short-range x-axis behavior:
  - `1M` uses day labels such as `May 18`, `May 25`, `Jun 1`
  - `6M` uses monthly labels such as `Dec 25`, `Jan 26`, `Feb 26`

Frontend BFF route:

- `frontend/src/app/api/metrics/[kind]/route.ts`

Frontend API client:

- `frontend/src/lib/api.ts`

## Latest verification

Backend:

- Targeted ruff on changed backend signal/fee files: passed
- Targeted tests: `28 passed, 1 warning`
- Full backend suite: `124 passed, 1 warning`

Live checks after Bitcoin Card-only cleanup:

- `GET /api/fees/history/1w`: `200`
- `GET /api/fees/profile?cadence=weekly&buyAmountUsd=100`: `200`
- `GET /api/metrics/summary`: `200`
- `POST /api/decisions/run`: `200`

Frontend:

- Targeted ESLint for valuation UI changes passed when last run.
- `npm run build` passed when last run.
- Build emits a known Recharts warning during static prerendering about width/height; build still succeeds.

## Current running preview services

At handoff, preview services were running on the VPS:

- SteadyStack frontend: `http://187.124.210.10:3003/`
- SteadyStack backend: `http://187.124.210.10:8000/`
- Bitcoin Card local HTTP API: `http://127.0.0.1:8787`

Known process IDs at handoff may be stale by the time a new session starts:

- SteadyStack backend: `proc_e54ef626ccbe`
- Bitcoin Card local HTTP: `proc_835213592dff`
- SteadyStack frontend last restarted several times; check with process list or restart if needed.

If the UI is not responding, prefer the production frontend server on port `3003`, not the Next dev server on `3002`.

## Current untracked local files

Expected untracked items:

- `backend/uv.lock`
  - generated by `uv run`
  - do not commit unless intentionally adopting uv lockfiles
- `sketches/`
  - temporary live-preview sketch directory
  - committed design artifacts are under `docs/ui-sketches/`

## Important Bitcoin Card context

Bitcoin Card repo:

- `https://github.com/zartyblartfast/bitcoin-card`
- Local clone used previously: `/tmp/bitcoin-card-inspect`
- Authoritative doc: `docs/bitcoin-card-api-usage.md`

Bitcoin Card local HTTP endpoints now include:

- `GET /api/summary`
- `GET /api/fee-history?range=24h|3d|1w|1m|3m|6m|1y|2y|3y`
- `GET /api/fee-profile?cadence=daily|weekly|monthly&buyAmountUsd=100&targetVbytes=140`
- `GET /api/bitcoin-risk`
- `GET /api/bmri-comparison`

Bitcoin Card MCP tools include:

- `get_dca_metrics`
- `get_fee_history`
- `get_fee_profile`
- `get_bitcoin_risk`
- `get_bitcoin_mean_reversion_index`
- `get_network_summary`
- `get_bitcoin_price`
- `get_mempool_fees`

## Recommended next work

Good next step:

1. Verify the existing `Fees` tab visually now that `/api/fees/history/{period}` uses Bitcoin Card.
2. Add frontend use of `/api/fees/profile` so the Fees tab can show:
   - recommended sat/vB
   - estimated fee USD
   - fee as % of planned buy
   - confidence/regime/reason
3. Keep fee display hierarchy:
   - fee % of buy first
   - estimated USD fee second
   - sat/vB third
4. Then decide whether to continue with:
   - campaign API endpoints using the in-memory repository, or
   - production campaign UI.

## Commands likely useful next session

Backend tests:

```bash
cd /tmp/SteadyStack-inspect/backend
./.venv/bin/pytest tests/ -q
```

Targeted backend lint/tests:

```bash
cd /tmp/SteadyStack-inspect/backend
./.venv/bin/ruff check app/signals app/api/fees.py tests/test_signals tests/test_fees_api.py
./.venv/bin/pytest tests/test_signals tests/test_fees_api.py -q
```

Frontend checks:

```bash
cd /tmp/SteadyStack-inspect/frontend
npx eslint src/components/ValuationContextPanel.tsx src/app/page.tsx src/lib/api.ts 'src/app/api/metrics/[kind]/route.ts'
npm run build
```

Run SteadyStack backend:

```bash
cd /tmp/SteadyStack-inspect/backend
uv run --extra dev uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run SteadyStack frontend production preview:

```bash
cd /tmp/SteadyStack-inspect/frontend
BACKEND_URL=http://127.0.0.1:8000 npm run start -- --hostname 0.0.0.0 --port 3003
```

Run Bitcoin Card local HTTP API:

```bash
cd /tmp/bitcoin-card-inspect
COREPACK_ENABLE_DOWNLOAD_PROMPT=0 corepack pnpm install
COREPACK_ENABLE_DOWNLOAD_PROMPT=0 corepack pnpm -r build
node examples/bitcoin-card-dashboard/server.mjs
```
