# SteadyStack DOX

## Purpose

This repository is evolving SteadyStack from a fee-aware Bitcoin DCA prototype into a campaign-based Bitcoin accumulation platform.

DOX keeps agent work aligned with the project rules. Before editing, read this file and every child `AGENTS.md` on the path to files you will touch. After meaningful changes, update the nearest applicable `AGENTS.md` if purpose, workflow, contracts, verification, or durable rules changed.

## Ownership

Root owns project-wide product, security, workflow, and documentation rules. Child AGENTS files own local implementation details.

## Local Contracts

- Branch for campaign-platform work: `feature/campaign-platform`.
- Do not wipe `main`; keep it as the stable v0.2 fee-aware DCA prototype baseline.
- v0.3 source-of-truth spec: `docs/specs/campaign-platform-v0.3.md`.
- UI/design artifacts: `docs/ui-sketches/campaign-ui-v2/` and `docs/ui-sketches/campaign-ui-v3/`.
- SteadyStack is campaign-based: Core DCA, Bear Market Boost, Fixed-Term DCA.
- Advisory-first. Hosted/VPS monitoring is likely needed for reliable alerts for laptop users.
- Automation is later-stage only and must use restricted trade-only exchange API keys; withdrawal-enabled credentials must be rejected.
- Never handle seed phrases, private keys, server-held wallets, or withdrawal-enabled credentials.
- BMRI and Bitcoin Risk are valuation context, not automated trading signals.
- Fee optimisation is default for every campaign and must account for sat/vB, estimated USD fee, and fee as % of planned buy.
- Use plain language first, technical detail second.

## Work Guidance

- Prefer TDD for backend implementation: failing test first, minimal implementation, then refactor.
- Keep implementation slices small and commit/push clean pause baselines.
- Do not commit generated `backend/uv.lock` unless the project intentionally adopts uv lockfiles.
- Preserve source/caveat metadata from Bitcoin Card rather than hiding it.
- Avoid broad production UI work until backend contracts are stable.

## Verification

Backend:

```bash
cd backend
uv run --extra dev pytest tests/ -q
```

Focused checks should use the closest relevant tests plus targeted ruff checks on changed files.

## Child DOX Index

- `backend/AGENTS.md` — backend/FastAPI/testing/package rules.
- `backend/app/campaigns/AGENTS.md` — campaign domain state, events, repository, future APIs.
- `backend/app/signals/AGENTS.md` — Bitcoin Card and signal adapter rules.
- `frontend/AGENTS.md` — UI language, BFF/frontend conventions, sketch-derived presentation rules.
- `docs/AGENTS.md` — specification, sketch, and planning document rules.
