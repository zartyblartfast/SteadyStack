# SteadyStack Frontend

Next.js 16 + React 19 frontend for SteadyStack — a fee-aware, non-custodial Bitcoin DCA platform.

## Quick Start

```bash
npm install
npx next dev -p 3002
```

Open [http://localhost:3002](http://localhost:3002). The backend must be running on port 8000 for the Fees tab to work.

## Architecture

The frontend is a single-page app with 4 tabs:

| Tab | Component | Backend? |
|---|---|---|
| **Fees** | `FeeMonitorPanel` | Yes — calls `/api/decisions/run` for live fee data |
| **Evidence** | `EvidencePanel` | No — static backtesting results |
| **Projection** | `WhatIfPanel` | No — client-side computation (`lib/projection.ts`) |
| **Infrastructure** | `InfrastructurePanel` | No — educational content |

### Backend Communication

All backend calls go through Next.js API proxy routes (BFF pattern, see ADR-014):

```
Browser → /api/decisions/run (Next.js route) → http://localhost:8000/api/decisions/run (FastAPI)
```

The browser never calls the backend directly. Proxy routes are in `src/app/api/`.

### Environment Variables

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `BACKEND_URL` | Server-side (proxy routes) | `http://localhost:8000` | Backend URL for API proxying |
| `NEXT_PUBLIC_API_URL` | Client-side (`lib/api.ts`) | `""` (same origin) | API base URL for client-side calls |

## Stack

- **Next.js 16** (App Router, Turbopack)
- **React 19**
- **Tailwind CSS v4** (dark theme with CSS custom properties)
- **Recharts 3** (charts in Evidence and Projection tabs)
- **Lucide** (icons)
