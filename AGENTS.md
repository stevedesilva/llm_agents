# AGENTS.md

Compact repo guide for coding agents. Keep edits narrow and follow verified commands/contracts.

## Scope and instruction sources
- Applies repo-wide; for `desilvaware/dsa_tester/**`, also follow `desilvaware/dsa_tester/CLAUDE.md`.
- Additional guidance source: `CLAUDE.md`.
- No `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, or repo `opencode.json` currently present.

## Stack and layout (high-value)
- Python `>=3.12` managed with `uv` (`pyproject.toml`).
- Shared core in `arena/` (provider querying + judging), used by both app entrypoints and tests.
- Arena entrypoints: `desilvaware/best_answer/app.py` (Gradio) and `desilvaware/best_answer/main.py` (CLI).
- DSA app: FastAPI backend in `desilvaware/dsa_tester/server.py` + React/Vite frontend in `desilvaware/dsa_tester/frontend/`.
- Frontend dev server proxies `/api` to `http://127.0.0.1:8001` (`desilvaware/dsa_tester/frontend/vite.config.ts`).

## Setup and run
- Install Python deps: `uv sync`
- Env: `cp .env.example .env` (at least `OPENAI_API_KEY` required for core flows)
- Install DSA frontend deps: `npm install --prefix desilvaware/dsa_tester/frontend`
- Run arena web UI: `uv run python desilvaware/best_answer/app.py`
- Run arena CLI: `uv run python desilvaware/best_answer/main.py`
- Run DSA backend: `uv run python desilvaware/dsa_tester/server.py`
- Run DSA frontend: `npm run dev --prefix desilvaware/dsa_tester/frontend`

## Verification commands
- Full lint: `uv run ruff check .`
- Full tests: `uv run pytest`
- Fast loop: `uv run ruff check . && uv run pytest -q`
- Arena-focused tests: `uv run pytest tests/test_providers.py tests/test_judge.py -v`
- DSA-focused tests: `uv run pytest tests/dsa_tester/ -q`
- DSA frontend build/typecheck: `npm run build --prefix desilvaware/dsa_tester/frontend`

## Contracts agents should not break
- Keep provider fan-out/judging flow concurrent (`asyncio.gather` + `asyncio.to_thread` pattern in arena and DSA paths).
- Reuse cached client factories in `arena/providers.py` (`_get_openai_client`, `_get_anthropic_client`); do not instantiate ad-hoc clients repeatedly.
- Parse LLM JSON via `arena.judge.extract_json()` before `json.loads()` when consuming model output.
- DSA submit stream must stay SSE-formatted as `data: {json}\n\n` with event names `running`, `case_result`, `evaluating_explanation`, `complete`.
- Never expose `hidden_test_cases` in API responses from `/api/question`.
- Never execute user submissions in-process; keep subprocess-based execution in `desilvaware/dsa_tester/runner.py` path.
- In async DSA server code, keep DB access thread-wrapped (no direct blocking `sqlite3` calls in async handlers).

## Testing quirks worth remembering
- `pytest-asyncio` runs in strict mode (`pyproject.toml`).
- `tests/conftest.py` clears provider client `lru_cache` automatically; preserve this behavior when touching provider tests.
