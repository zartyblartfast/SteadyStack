# Docs DOX

## Purpose

`docs/` owns product specifications, planning documents, architecture notes, and disposable UI sketch artifacts that preserve design decisions.

## Ownership

This file applies to `docs/`.

## Local Contracts

- v0.3 source-of-truth spec: `docs/specs/campaign-platform-v0.3.md`.
- Design evolution and rationale: `docs/campaign-platform-evolution.md`.
- UI sketch artifacts are preserved under `docs/ui-sketches/`.
- Specs should be operational and implementation-facing, not diary entries.
- Preserve decisions and invariants, especially:
  - DCA first, optimise second.
  - advisory-first.
  - BMRI and Bitcoin Risk are context, not trading signals.
  - fee % first.
  - no silent unsafe campaign transitions.
  - no withdrawal-enabled automation credentials.
- When a code change alters durable behavior, update the relevant spec/plan if it changes the contract.

## Work Guidance

- Keep docs concise and current.
- Do not keep polishing old sketch rounds; create a new round only for a specific unresolved design question.
- Prefer adding short appraisal/decision sections over rewriting history.
- Link implementation phases to concrete files/tests when possible.

## Verification

No automated docs verification yet. For docs-only changes, verify paths and links manually where practical.

## Child DOX Index

No child DOX files yet.
