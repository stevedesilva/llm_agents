# AGENTS.md

Compact, high-signal repo notes for coding agents.

## Scope
- Applies repo-wide; when editing `desilvaware/dsa_tester/**`, also follow `desilvaware/dsa_tester/CLAUDE.md`.
- Also read root `CLAUDE.md` for run/validation context.

## Repo shape (what matters)
- Python package code is in `arena/` and `desilvaware/` (`pyproject.toml` wheel packages); `1_foundations/` are lab scripts.
- Arena entrypoints: `desilvaware/best_answer/app.py` (Gradio UI) and `desilvaware/best_answer/main.py` (CLI).
- DSA Tester is split: backend `desilvaware/dsa_tester/server.py` (FastAPI, port 8001) + frontend `desilvaware/dsa_tester/frontend/` (Vite, port 5174).
- Frontend dev proxy sends `/api` to `http://127.0.0.1:8001` (`desilvaware/dsa_tester/frontend/vite.config.ts`).

## Setup and run
- Install Python deps: `uv sync`
- Create env file: `cp .env.example .env` (minimum key for core flows: `OPENAI_API_KEY`)
- Install DSA frontend deps: `npm install --prefix desilvaware/dsa_tester/frontend`
- Run arena UI: `uv run python desilvaware/best_answer/app.py`
- Run arena CLI: `uv run python desilvaware/best_answer/main.py`
- Run DSA backend: `uv run python desilvaware/dsa_tester/server.py`
- Run DSA frontend: `npm run dev --prefix desilvaware/dsa_tester/frontend`

## Verification (fastest useful commands)
- Full repo lint/tests: `uv run ruff check . && uv run pytest -q`
- Arena only: `uv run pytest tests/test_providers.py tests/test_judge.py -v`
- DSA backend tests: `uv run pytest tests/dsa_tester/ -q`
- Single test file: `uv run pytest tests/test_judge.py -v`
- DSA frontend typecheck/build: `npm run build --prefix desilvaware/dsa_tester/frontend`

## Contracts you should preserve
- Keep arena query/judging concurrency: `asyncio.gather(...)` + `asyncio.to_thread(...)` (`desilvaware/best_answer/*`, `arena/judge.py`).
- Reuse cached clients in `arena/providers.py` (`_get_openai_client`, `_get_anthropic_client`); avoid ad-hoc client creation.
- `arena.judge.extract_json()` returns a JSON string, not a dict; parse it before key access.
- DSA `/api/question` must never return `hidden_test_cases` (server strips this before response).
- DSA submit streaming must remain SSE `data: {json}\n\n`; primary events are `running`, `case_result`, `evaluating_explanation`, `complete` (plus `error` on missing session).
- Keep user code execution subprocess-based in `desilvaware/dsa_tester/runner.py` (no in-process `exec`/`eval`).
- In async DSA paths, keep SQLite work behind `asyncio.to_thread(...)` wrappers (`desilvaware/dsa_tester/db.py`).

## Testing quirks
- `pytest-asyncio` strict mode is enabled (`pyproject.toml`), so async tests must be explicitly marked/awaited correctly.
- `tests/conftest.py` clears provider client `lru_cache` around each test; preserve this when modifying provider tests.
