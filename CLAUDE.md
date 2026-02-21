# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM Arena is a Python tool that benchmarks multiple LLM providers by sending them the same question concurrently, having each provider judge all responses, and producing a crowd-sourced leaderboard. It uses `uv` as the package manager and Python 3.12+.

## Commands

```bash
# Install dependencies
uv sync

# Run the Gradio web UI (main entry point)
uv run python desilvaware/best_answer/app.py

# Run the CLI interactive arena
uv run python desilvaware/best_answer/main.py

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

The core logic lives in `arena/` and is imported by both entry points:

- `arena/providers.py` — `Provider` dataclass, `query_provider()`, `validate_api_keys()`, cached OpenAI/Anthropic client factories
- `arena/judge.py` — `judge_all()`, `average_rankings()`, prompt construction, JSON extraction from LLM responses
- `arena/display.py` — `rich`-based console output helpers
- `arena/config.py` — constants: `DEFAULT_PROVIDERS`, `CLARIFICATION_MODEL`, `MAX_CLARIFICATION_ROUNDS`, `QUERY_TIMEOUT`

### Entry points

- `desilvaware/best_answer/app.py` — Gradio web UI: chat-style question clarification then arena run
- `desilvaware/best_answer/main.py` — CLI version with the same clarification → arena flow
- `main.py` — placeholder root entry point (not the real entry point)

### Data flow

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
| `OPENAI_API_KEY` | GPT models + question generation (required) |
| `ANTHROPIC_API_KEY` | Claude Sonnet 4.5 (optional) |
| `GOOGLE_API_KEY` | Gemini 2.5 Flash (optional) |
| `DEEPSEEK_API_KEY` | DeepSeek Chat (optional) |
| `GROQ_API_KEY` | Groq (optional) |

Ollama requires no key but needs a local server on port 11434.

## After Every Code Change

Run the following to validate the build before committing:

```bash
uv run ruff check .
uv run pytest
```

Both must pass with no errors.

## Testing

Tests live in `tests/` and import from `arena/`. `conftest.py` provides `Provider` fixtures and clears `lru_cache` between tests to prevent cross-test contamination. Tests use `pytest-asyncio` in strict mode (`asyncio_mode = "strict"` in `pyproject.toml`).
