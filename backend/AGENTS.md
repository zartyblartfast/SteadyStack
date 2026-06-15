# Backend DOX

## Purpose

Backend owns FastAPI APIs, Bitcoin metrics integration, campaign domain logic, persistence, and future monitoring/automation support.

## Ownership

This file applies to `backend/` unless a deeper `AGENTS.md` applies.

## Local Contracts

- Python 3.12 backend using FastAPI, Pydantic, SQLAlchemy models, pytest, and uv.
- Keep browser-facing contracts behind backend/BFF APIs; do not expose raw third-party payloads directly unless explicitly intended.
- `backend/pyproject.toml` has explicit setuptools package discovery for the current flat layout:
  ```toml
  [tool.setuptools.packages.find]
  include = ["app*"]
  ```
- Existing golden tests require `PyYAML` in dev dependencies.
- Do not commit generated `backend/uv.lock` unless uv lockfiles are intentionally adopted.
- Existing full-repo ruff has pre-existing findings; run ruff on changed files unless doing lint cleanup.

## Work Guidance

- Use TDD for new behavior.
- Add focused tests near the changed domain/API before implementation.
- Return stable normalized API shapes; keep third-party quirks behind adapters.
- Surface safe 502-style errors for upstream metrics failures.
- Treat security-sensitive automation as future work; no exchange API credential storage yet.

## Verification

Full backend suite:

```bash
uv run --extra dev pytest tests/ -q
```

Focused examples:

```bash
uv run --extra dev pytest tests/test_signals/test_bitcoin_card.py -q
uv run --extra dev pytest tests/test_metrics_api.py -q
uv run --extra dev pytest tests/test_campaigns -q
uv run --extra dev ruff check app/campaigns tests/test_campaigns
```

## Child DOX Index

- `app/campaigns/AGENTS.md` — campaign schemas/state/events/repository/API rules.
- `app/signals/AGENTS.md` — Bitcoin Card and signal adapter rules.
