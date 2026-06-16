# Frontend DOX

## Purpose

Frontend owns the user experience for campaign setup, advisory alerts, metrics display, reports, and future monitoring/automation controls.

## Ownership

This file applies to `frontend/`.

## Local Contracts

- The app should feel like a calm Bitcoin accumulation planner, not a trading terminal.
- Use plain English first; reveal technical detail one layer deeper.
- BMRI copy: lead with "Bitcoin looks historically cheap/neutral" before P10/P5 detail.
- Bitcoin Risk copy: present as valuation-risk context, not a trading signal.
- Fee display hierarchy: fee as % of planned buy first, estimated USD fee second, sat/vB third.
- Mobile rule: one decision per screen.
- For hosted/advisory trust UX, be explicit about what is stored and what is never stored.
- Automation copy must state that only trade-only exchange keys are acceptable and withdrawal-enabled keys are rejected.
- Do not overload one god-page; prefer list -> detail -> edit/report patterns.

## Work Guidance

- Use the v3 sketches as design direction, not production code to copy verbatim.
- Production UI should consume stable backend APIs rather than hardcoded sketch data.
- Valuation UI consumes `/api/metrics/bmri` and `/api/metrics/bitcoin-risk` via the Next.js BFF route `src/app/api/metrics/[kind]/route.ts`.
- Keep advanced BMRI/fee settings collapsed or secondary by default.
- Show source/caveat/fetchedAt details where metrics are used.
- Campaign reports should remain accessible after completion.

## Verification

Use project frontend scripts from `frontend/package.json` when touching frontend code. If adding tests/tooling, update this file with the exact command.

## Child DOX Index

No child DOX files yet.
