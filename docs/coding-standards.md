# Coding Standards

Practical standards for the SteadyStack codebase. These are not aspirational — they are enforced by tooling where possible and by code review where not.

---

## Python (Backend)

### Tooling

| Tool | Purpose | Config |
|---|---|---|
| **Ruff** | Linting + formatting (replaces Black, isort, flake8) | `pyproject.toml` |
| **mypy** | Static type checking (strict mode) | `pyproject.toml` |
| **pytest** | Testing | `pyproject.toml` |

These run in CI. Code that fails linting or type checking does not merge.

### Type Hints

Every function signature has type hints. No exceptions.

```python
# Good
def evaluate_fee_signal(fee_rate: float, threshold: float) -> SignalScore:
    ...

# Bad — missing types
def evaluate_fee_signal(fee_rate, threshold):
    ...
```

Use Pydantic `BaseModel` for all data structures that cross module boundaries (API requests/responses, signal snapshots, decision objects). Use `dataclass` for internal-only structures where Pydantic validation is unnecessary.

### Module Boundaries

This is the most important standard in the project. Modules communicate through **defined interfaces**, not by reaching into each other's internals.

```
signals/  →  policy/  →  engine/  →  explain.py
```

**Rules:**
- `signals/` exports a `SignalSnapshot` dataclass. It knows nothing about policy or decisions.
- `policy/` accepts a `SignalSnapshot` and returns a `PolicyResult`. It knows nothing about where signals came from or how decisions are delivered.
- `engine/` orchestrates the pipeline. It does not contain business logic — only sequencing.
- Imports flow **left to right** in the pipeline. Never backwards. `policy/` never imports from `engine/`. `signals/` never imports from `policy/`.
- `api/` may import from any module to wire things together. No other module imports from `api/`.

**How to check:** If you need to import from a module to its left in the pipeline, you are breaking the dependency direction. Refactor by extracting a shared type into a `types.py` or `schemas.py` at the appropriate level.

### Function Design

- **Pure functions for policy logic.** Given the same inputs, they must return the same output. No side effects, no I/O, no global state. This is essential for testing and backtesting.
- **Small functions with a single responsibility.** If a function does two things, split it.
- **Explicit over implicit.** Pass dependencies as arguments rather than importing singletons. This makes testing straightforward.

```python
# Good — pure, testable
def score_fee_signal(fee_rate: float, profile: StrategyProfile) -> SignalScore:
    if fee_rate <= profile.fee_threshold_low:
        return SignalScore(value=1.0, reason="Fees below low threshold")
    ...

# Bad — hidden dependency, hard to test
def score_fee_signal(fee_rate: float) -> SignalScore:
    profile = get_current_profile()  # implicit global state
    ...
```

### Error Handling

- **Never silently swallow exceptions.** Always log or re-raise.
- **Use specific exception types.** Define project exceptions in a `exceptions.py` per module where needed (e.g., `signals/exceptions.py`).
- **External API calls always have timeouts and fallback behaviour.** Never let a third-party hang the pipeline.

```python
class SignalFetchError(Exception):
    """Raised when an external data source is unreachable or returns invalid data."""
    pass

class StaleDataError(SignalFetchError):
    """Raised when cached data exceeds its maximum acceptable age."""
    pass
```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions and variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private functions**: prefix with `_` only if they are genuinely internal to a module and not tested directly

### Configuration

- All config loaded via Pydantic `BaseSettings` in `config.py`.
- No hardcoded URLs, thresholds, or credentials anywhere in the codebase.
- Policy thresholds are config, not magic numbers. They live in strategy profile definitions, not buried in logic functions.

---

## TypeScript (Frontend)

### Tooling

| Tool | Purpose |
|---|---|
| **ESLint** | Linting (Next.js default config + strict TypeScript rules) |
| **Prettier** | Formatting |
| **TypeScript** | Strict mode enabled |

### Standards

- **Strict TypeScript** — `strict: true` in `tsconfig.json`. No `any` types without an explicit comment explaining why.
- **React components** — functional components only, named exports.
- **API client** — all backend calls go through a single API client in `lib/api.ts`. Components never call `fetch` directly.
- **Styling** — Tailwind CSS utility classes. No inline styles. Shared component library via shadcn/ui.
- **State** — prefer server components where possible. Client state via React hooks. No global state library unless complexity demands it.

---

## Testing

### Backend

- **Policy and scoring tests are mandatory.** Every rule, threshold, and scoring function must have tests covering normal, edge, and boundary cases. These are the most important tests in the project.
- **Signal tests use mocked HTTP responses.** Never hit real APIs in tests. Use `pytest` fixtures with recorded responses.
- **Engine/pipeline tests are integration tests.** They wire together real policy logic with mocked signals to verify end-to-end decision correctness.
- **Test file naming**: `test_<module>.py` mirroring the source structure.

```python
# Example: testing a policy rule
def test_skip_when_fees_above_threshold():
    snapshot = SignalSnapshot(fee_rate=85.0, ...)
    profile = StrategyProfile(fee_threshold_high=80.0, ...)
    result = evaluate_policy(snapshot, profile)
    assert result.action == Action.SKIP
    assert "fee" in result.reason.lower()
```

### Frontend

- **Vitest** for unit tests.
- **Component tests** for any component with non-trivial logic.
- **E2E tests** (Playwright) added when the dashboard is functional — not needed in early phases.

---

## Git & Workflow

- **Commit messages**: imperative tense, concise. `Add fee signal scoring` not `Added fee signal scoring` or `This commit adds fee signal scoring`.
- **Branch naming**: `feature/<short-description>`, `fix/<short-description>`, `docs/<short-description>`.
- **One concern per commit.** Don't mix a bug fix with a new feature.
- **Never commit `.env`**, secrets, or API keys. The `.gitignore` already handles this.

---

## Key Principle

> If the deterministic policy logic is not independently testable with a single function call and no I/O setup, the architecture has a bug.

This is the north star. Every design decision in the backend should preserve this property.
