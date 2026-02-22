# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@desilvaware/best_answer/README.md
@1_foundations/lab2/README.md

## Project Overview

LLM Agents is a Python project with learning labs and an LLM Arena that benchmarks multiple providers by sending them the same question concurrently, having each provider judge all responses, and producing a crowd-sourced leaderboard. It uses `uv` as the package manager and Python 3.12+.

## Commands

```bash
# Install dependencies
uv sync

# Run the Gradio web UI (main entry point)
uv run python desilvaware/best_answer/app.py

# Run the CLI interactive arena
uv run python desilvaware/best_answer/main.py

# Run the auto-generated question arena (lab2)
uv run python 1_foundations/lab2/main.py

# Run the basic OpenAI interaction lab
uv run python 1_foundations/lab1/start.py

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_providers.py -v

# Run with coverage
uv run pytest --cov=arena

# Lint
uv run ruff check .

# Add / remove dependencies
uv add <package>
uv remove <package>
```

## Architecture

### Shared `arena/` package

The core logic lives in `arena/` and is imported by all entry points:

- `arena/config.py` — `DEFAULT_PROVIDERS`, `CLARIFICATION_MODEL`, `MAX_CLARIFICATION_ROUNDS`, `MAX_CLARIFY_ANSWER_LENGTH`
- `arena/providers.py` — `Provider` dataclass, `query_provider()`, `validate_api_keys()`, cached OpenAI/Anthropic client factories, `QUERY_TIMEOUT`, `MAX_INPUT_LENGTH`
- `arena/judge.py` — `judge_all()`, `average_rankings()`, prompt construction, JSON extraction from LLM responses
- `arena/display.py` — `rich`-based console output helper

### Entry points

- `desilvaware/best_answer/app.py` — Gradio web UI: chat-style question clarification then arena run
- `desilvaware/best_answer/main.py` — CLI version with the same clarification → arena flow
- `1_foundations/lab2/main.py` — Auto-generated question arena (no user clarification, uses its own provider list)
- `1_foundations/lab1/start.py` — Basic OpenAI interaction patterns (learning lab)
- `main.py` — placeholder root entry point

### Data flow (desilvaware/best_answer)

1. User submits a question
2. GPT iteratively clarifies the question (up to `MAX_CLARIFICATION_ROUNDS`)
3. All available providers are queried concurrently via `asyncio.gather` + `asyncio.to_thread`
4. Each answering provider also acts as a judge, ranking all answers concurrently
5. Rankings are averaged across all judges to produce a final leaderboard

### Provider abstraction

Providers are configured with `kind="openai"` or `kind="anthropic"`. OpenAI-compatible providers (Gemini, DeepSeek, Groq, Ollama) all use the OpenAI client with a custom `base_url`, so only two code paths exist. Missing API keys cause providers to be skipped gracefully.

## Configuration

API keys go in `.env` (copy from `.env.example`):

| Variable | Provider |
|---|---|
| `OPENAI_API_KEY` | GPT models + question clarification (required) |
| `ANTHROPIC_API_KEY` | Claude Opus 4.6 (optional) |
| `GOOGLE_API_KEY` | Gemini 3.0 Flash (optional) |
| `DEEPSEEK_API_KEY` | DeepSeek Chat (optional) |
| `GROQ_API_KEY` | Groq (optional) |

Lab2 also supports Ollama (no key needed, requires local server on port 11434).

## After Every Code Change

Run the following to validate the build before committing:

```bash
uv run ruff check .
uv run pytest
```

Both must pass with no errors.

## Testing

Tests live in `tests/` and import from `arena/`. `conftest.py` provides `Provider` fixtures and clears `lru_cache` between tests to prevent cross-test contamination. Tests use `pytest-asyncio` in strict mode (`asyncio_mode = "strict"` in `pyproject.toml`).
