# Signals DOX

## Purpose

`backend/app/signals/` owns external Bitcoin metric collection and normalization, including Bitcoin Card integration.

## Ownership

This file applies to signal collectors/adapters under `backend/app/signals/` and related tests under `backend/tests/test_signals/`.

## Local Contracts

- Bitcoin Card is intended to become SteadyStack's single Bitcoin metrics source.
- Bitcoin Card API doc: `docs/bitcoin-card-api-usage.md` in `https://github.com/zartyblartfast/bitcoin-card`.
- Bitcoin Card v0.1.x has no hosted public API.
- Current SteadyStack HTTP adapter covers:
  - `GET /api/summary`
  - `GET /api/bmri-comparison`
- Bitcoin Card local HTTP also exposes `GET /api/bitcoin-risk`; SteadyStack adapter/API support is a follow-up.
- Bitcoin Card MCP exposes richer context:
  - `get_dca_metrics`
  - `get_bitcoin_risk` with composite components and daily `history[]`
  - `get_bitcoin_mean_reversion_index`
- Preserve source metadata: `fetchedAt`, source names, `sourceQuality`, caveats, methodology, limitations, and data dates.
- Do not treat BMRI or Bitcoin Risk as automated trading signals.
- When normalizing numeric fields, never use truthy `or` fallback; `0.0` is a valid BMRI/Risk value. Use presence-aware key lookup.
- Upstream failures should raise `SignalFetchError` and be mapped by APIs to safe user-facing errors.

## Work Guidance

- Keep adapter outputs stable and internal; hide raw response shape behind dataclasses/models.
- Add mocked-payload tests for success, HTTP failure, malformed data, and valid zero values.
- Treat Bitcoin Risk initially as valuation context, not as a trigger or blended score.
- If local HTTP adds DCA/risk endpoints later, extend the adapter with tests before API changes.

## Verification

```bash
cd backend
uv run --extra dev pytest tests/test_signals/test_bitcoin_card.py -q
uv run --extra dev ruff check app/signals/bitcoin_card.py tests/test_signals/test_bitcoin_card.py
```

## Child DOX Index

No child DOX files yet.
