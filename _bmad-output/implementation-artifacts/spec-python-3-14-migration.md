---
title: 'Require Python 3.14, drop 3.12/3.13 support'
type: 'chore'
created: '2026-09-18'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - _bmad-output/planning-artifacts/architecture.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The project declares Python `>=3.12`, runs CI on 3.12/3.13, and ships a `python:3.13-slim` Docker image. The app must move to Python 3.14 and drop all 3.12/3.13 compatibility.

**Approach:** Bump every Python version declaration to 3.14 (pyproject `requires-python` and ruff `target-version`, `.python-version`, Dockerfile base image, all GitHub workflow Python pins/matrices, user-guide selfhosting doc, architecture planning doc), regenerate `uv.lock`, verify the full CI suite locally on Python 3.14, and deliver as a breaking-change commit (`feat!:` + `BREAKING CHANGE:` footer) on a new branch with an open PR.

</frozen-after-approval>

## Implementation Notes

- 2026-09-18: Branch `feature/python-3.14` off `master` (27aa67c). Changed: `pyproject.toml` (requires-python `>=3.14`, ruff `target-version = "py314"`), `.python-version` → 3.14, `Dockerfile` → `python:3.14-slim`, `ci.yml` matrix → `['3.14']` (comment rewritten: 3.14 is floor and Docker runtime), `docs.yml` and `uv-lock-refresh.yml` pins → 3.14, `user-guide/docs/selfhosting.md` → "Python 3.14+", `_bmad-output/planning-artifacts/architecture.md` lines 42/58 → "Python 3.14+", `uv.lock` regenerated (61 packages resolved cleanly, no dependency needed a bump for 3.14).
- Surprise: with `target-version = "py314"`, ruff format applies PEP 758 and rewrote `except (asyncio.CancelledError, Exception):` → `except asyncio.CancelledError, Exception:` in `tests/api/test_mcp.py` and `tests/api/test_mcp_tools.py`. Valid 3.14-only syntax; required for `ruff format --check` to pass.
- Verification on CPython 3.14.7: `uv lock --check` OK, `ruff check` OK, `ruff format --check` OK, `ty check` OK, pytest unit 88 passed / api 123 passed 6 skipped / integration 36 passed 2 skipped. Full CI chain green.
- Known third-party noise: slowapi 0.1.10 emits `DeprecationWarning: asyncio.iscoroutinefunction is deprecated ... removal in Python 3.16`. Not actionable in this migration (upstream dependency).
- Review round (Blind Hunter, 11 findings): patched markupsafe lock entry 3.0.2→3.0.3 (3.0.2 had zero cp314 wheels → sdist-only in lock → would build from source in compiler-less python:3.14-slim; verified end-to-end: podman image build OK, `markupsafe._speedups` C extension active in-container), updated `_bmad-output/project-context.md:29` Python floor (missed by planning sweep), added `Programming Language :: Python :: 3.14` trove classifier to pyproject. Empirically disproven findings: coverage 7.10.6 works on 3.14 (full test-cov chain green, 79% total); mkdocs stack (unpinned requirements.txt) installs and builds on 3.14 in a throwaway venv; Docker image builds cleanly via podman. Deferred: stale dep-version tables in planning docs; ubuntu-22.04 runner retirement. Re-verified after patches: uv lock --check, ruff check/format, ty, and all three pytest suites green.

- Post-review follow-up (same branch, review nit from PR #285): closed the stale-version-tables deferral with a one-pass sync of `_bmad-output/planning-artifacts/architecture.md` (FastAPI, Uvicorn, Pony, Pydantic Settings, Redis, Prometheus Client, Ruff, SlowAPI, httpx casing) and `_bmad-output/project-context.md` (FastAPI, Uvicorn, Pony, Pydantic Settings, validators, Redis, Prometheus Client, SlowAPI, Ruff, pytest stack) against pyproject pins; removed the corresponding `deferred-work.md` entry. Docs-only, no CI surface (ruff excludes `_bmad-output`).

## Review Triage Log

- markupsafe 3.0.2 sdist-only in lock (no cp314 wheels) → **high** — verified in uv.lock entry (0 wheels) and PyPI; patched via `uv lock --upgrade-package markupsafe` → 3.0.3 (22 cp314 wheels); confirmed only affected package by scanning all lock entries; in-container C-extension import proves the fix.
- project-context.md still declared "Python 3.12+" → **medium** — verified tracked file at line 29; patched the Python floor; stale FastAPI/Uvicorn rows in the same table deferred (pre-existing).
- Stale dependency version tables in planning docs (architecture.md, project-context.md) vs pyproject pins → **medium, pre-existing** — not caused by this change; deferred.
- ci.yml single-element matrix called "dead machinery" → **low, rejected** — a 1-element matrix with `fail-fast: false` is harmless, conventional, and future-proofs adding 3.15; the rewritten comment accurately describes the pins.
- coverage 7.10.6 unproven on 3.14 / test-cov path → **false** — disproven by running the full test-cov chain locally on 3.14.7: all suites pass, report generated.
- Docker image build never exercised → **maybe-false → false** — settled by building the image with podman on python:3.14-slim: `uv sync --frozen` succeeds compiler-less and markupsafe C extension is active at runtime.
- Spec file untracked / frontmatter stale → **process, addressed** — file is committed with the branch and status set to done in this finalize step.
- Commit/push/PR not yet executed → **false as a defect** — that is the workflow's own Commit/Present phase, executed in this run.
- ubuntu-22.04 runner retirement track → **low, pre-existing** — deferred as separate infra work.
- docs.yml unpinned mkdocs requirements unverified on 3.14 → **false** — disproven by installing requirements.txt and running `mkdocs build` on 3.14 in a throwaway venv.
- Missing Python trove classifiers → **low → patched** — simple addition directly serving the migration intent; pip install refusal is already enforced by requires-python.

