# Campaigns DOX

## Purpose

`backend/app/campaigns/` owns campaign-domain logic for SteadyStack v0.3: campaign schemas, state transitions, events, repositories, and future campaign APIs/services.

## Ownership

This file applies to all files under `backend/app/campaigns/` and campaign tests under `backend/tests/test_campaigns/`.

## Local Contracts

- Campaigns are the primary product unit: Core DCA, Bear Market Boost, Fixed-Term DCA.
- State transitions must follow `docs/specs/campaign-platform-v0.3.md` §8.1.
- No silent `paused -> active` transition without explicit confirmation.
- `completed` and `stopped` are terminal by default; clone/create a new campaign instead of reactivating.
- If BMRI is stale while a campaign is waiting, remain `waiting`; do not move to `ready` until fresh BMRI confirms the trigger.
- Events are the audit trail. Important state changes, fee changes, BMRI triggers, data outages, missed periods, and automation issues should produce campaign events.
- Event text must be user-facing and plain-English.
- Fee-related events should lead with fee as % of planned buy, with sat/vB/USD as supporting details where needed.
- BMRI-related events should lead with plain language such as "Bitcoin looks historically cheap" before P10/P5 detail.
- The current repository is in-memory only; it is a bridge to API work, not final persistence.

## Work Guidance

- Keep domain code pure and testable; avoid FastAPI/database coupling in schemas/state/events/repository.
- Add or update tests before changing behavior.
- Prefer immutable/frozen Pydantic models for domain value objects unless mutation is deliberately required.
- Add new event types to the enum, tests, and factories together.
- Keep transition rules explicit; do not bury lifecycle behavior in ad-hoc API handlers.

## Verification

```bash
cd backend
uv run --extra dev pytest tests/test_campaigns -q
uv run --extra dev ruff check app/campaigns tests/test_campaigns
```

## Child DOX Index

No child DOX files yet.
