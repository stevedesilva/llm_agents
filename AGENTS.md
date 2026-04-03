# AGENTS.md
Guide for agentic coding tools in this repository.

## Scope
- Applies to the whole repo unless a deeper folder has stricter rules.
- For `desilvaware/dsa_tester/**`, also follow `desilvaware/dsa_tester/CLAUDE.md`.
- Keep changes narrow; avoid unrelated refactors.

## Rule files checked
- `.cursor/rules/`: not present.
- `.cursorrules`: not present.
- `.github/copilot-instructions.md`: not present.
- Active guidance sources: `CLAUDE.md`, `desilvaware/dsa_tester/CLAUDE.md`.

## Stack
- Python 3.12+
- Package manager: `uv`
- Lint: `ruff`
- Test: `pytest`, `pytest-asyncio` (strict mode)
- Arena web UI: Gradio
- DSA backend: FastAPI + SQLite
- DSA frontend: React + TypeScript + Vite + MUI

## Setup
- `uv sync`
- `cp .env.example .env`
- `npm install --prefix desilvaware/dsa_tester/frontend`

## Build/lint/test commands
- Full lint: `uv run ruff check .`
- Full tests: `uv run pytest`
- Fast loop: `uv run ruff check . && uv run pytest -q`
- Coverage (arena): `uv run pytest --cov=arena`
- DSA lint only: `uv run ruff check desilvaware/dsa_tester/`
- DSA tests only: `uv run pytest tests/dsa_tester/ -q`
- DSA frontend build: `npm run build --prefix desilvaware/dsa_tester/frontend`

## Run commands
- Arena Gradio app: `uv run python desilvaware/best_answer/app.py`
- Arena CLI app: `uv run python desilvaware/best_answer/main.py`
- DSA backend: `uv run python desilvaware/dsa_tester/server.py`
- DSA frontend dev: `npm run dev --prefix desilvaware/dsa_tester/frontend`
- Lab 1: `uv run python 1_foundations/lab1/start.py`
- Lab 2: `uv run python 1_foundations/lab2/main.py`

## Key paths
- `arena/`: shared provider + judging core used by apps and tests.
- `desilvaware/best_answer/`: Gradio and CLI entry points.
- `desilvaware/dsa_tester/`: FastAPI app, Elo logic, runner, DB.
- `desilvaware/dsa_tester/frontend/`: React frontend.
- `tests/`: Python test suites.

## Test targeting (single-test focus)
- Run one file: `uv run pytest tests/test_providers.py -v`
- Run one class: `uv run pytest tests/test_judge.py::TestJudgeAll -v`
- Run one test: `uv run pytest tests/test_judge.py::TestParseRanking::test_valid_ranking -v`
- Run DSA suite: `uv run pytest tests/dsa_tester/ -v`
- Filter by keyword: `uv run pytest -k "ranking and not timeout" -v`

## Code style guidelines

### Imports and module layout
- Python import order: stdlib, third-party, local.
- Prefer absolute imports from package roots (`arena`, `desilvaware...`).
- Keep concise module docstrings.
- Avoid wildcard imports.

### Formatting and readability
- Keep code `ruff`-clean.
- Match surrounding formatting style in touched files.
- Keep functions focused and reasonably short.
- Use named constants for repeated magic values.
- Keep comments for non-obvious intent; avoid narrating obvious code.

### Types
- Use Python 3.12 type syntax (`str | None`, `list[tuple[int, str]]`).
- Type public functions, including async returns.
- Use `Literal` for constrained string values.
- In TypeScript, keep strict types; avoid `any`.
- Prefer explicit interfaces/types for API payload shapes.

### Naming
- `snake_case`: Python functions, methods, variables.
- `PascalCase`: Python classes and TS React components.
- `UPPER_SNAKE_CASE`: module constants.
- Prefix internal Python helpers with `_`.

### Error handling
- Raise explicit exceptions for invalid state (`ValueError`, `RuntimeError`).
- Preserve causality with `raise ... from e` when wrapping parse/validation errors.
- In provider/judging fan-out, handle partial failures gracefully.
- Wrap external/slow calls with explicit timeout logic where applicable.
- Return actionable error messages that include context (provider name, key state, parse issue).

### Async and concurrency
- Use `asyncio.gather` for independent parallel operations.
- Use `asyncio.to_thread` for blocking work.
- In DSA async handlers, never do direct `sqlite3` calls; use thread-wrapped DB helpers.
- Reuse cached client factories (`lru_cache`) instead of recreating clients repeatedly.

### LLM and judging contracts
- Reuse `arena.providers._get_openai_client()` for OpenAI-compatible clients.
- Parse model outputs via `arena.judge.extract_json()` before JSON decode.
- Keep prompt boundary delimiters (`<question>`, `<response ...>`) to reduce injection risk.
- Keep provider key handling graceful: missing optional keys should skip cleanly.

### DSA backend contracts
- Keep SSE wire format exactly `data: {json}\n\n`.
- Never send `hidden_test_cases` to frontend.
- Never run user code in-process (`exec`/`eval` forbidden); always subprocess.
- Keep Elo floor and difficulty/K-factor behavior consistent in `elo.py`.
- Preserve API event names for `/api/submit` stream (`running`, `case_result`, `evaluating_explanation`, `complete`).

### Frontend contracts
- Keep shared models in `desilvaware/dsa_tester/frontend/src/types.ts` as source of truth.
- Keep network logic in `desilvaware/dsa_tester/frontend/src/api.ts`.
- Keep state-machine flow in `App.tsx`: `idle -> question_loaded -> coding -> submitting -> results`.
- Use MUI components and `sx` styling patterns already used by the project.
- On language switch, reset editor to the selected language signature stub.
- Ensure interval/timer effects clean up properly (for example `clearInterval`).

## Agent behavior expectations
- Prefer smallest safe change that satisfies the task.
- Do not alter public API shapes unless requested or required.
- If API/event shape changes are necessary, update backend + frontend + tests together.
- Preserve backwards compatibility for stream event names and payload keys when possible.
- Avoid introducing new dependencies unless justified.
- If adding dependencies, document install and validation commands.

## Testing conventions
- Put tests in `tests/` by domain (`tests/dsa_tester/`, `tests/test_judge.py`, etc.).
- Use `@pytest.mark.asyncio` for async tests.
- Mock provider/network interactions; do not call external APIs in tests.
- Keep tests deterministic and assert clear behavior.
- Preserve fixture behavior that clears cached provider clients between tests.

## Agent completion checklist
- Run lint + smallest relevant tests for changed files.
- For provider/judging changes: `uv run pytest tests/test_providers.py tests/test_judge.py -v`.
- For DSA frontend changes: `npm run build --prefix desilvaware/dsa_tester/frontend`.
- Update docs if command, API, or architecture contracts changed.
- Never commit secrets from `.env` or API keys/tokens.
