# LLM Arena - Project Specification

## Overview

LLM Arena is a Python CLI tool that benchmarks multiple LLM providers by sending them the same question concurrently, then having each provider judge all responses to produce a crowd-sourced leaderboard.

## Goals

- Compare response quality across LLM providers on the same question
- Eliminate single-judge bias by having every competitor also act as a judge
- Run all queries and judging concurrently for speed
- Support adding new providers with minimal configuration

## Architecture

```
llm_agents/
├── 1_foundations/
│   ├── lab1/             # Basic OpenAI interaction patterns
│   │   └── start.py
│   └── lab2/             # LLM Arena (auto-generated questions)
│       ├── main.py       # Orchestrator — generates question, queries, judges
│       ├── providers.py  # Provider registry and query abstraction
│       ├── judge.py      # Multi-judge ranking and averaging logic
│       └── display.py    # Rich markdown console output
├── desilvaware/
│   └── best_answer/      # Enhanced Arena (user questions + clarification)
│       ├── main.py       # Adds interactive question input and AI-driven clarification
│       ├── providers.py  # Same provider registry
│       ├── judge.py      # Same judging logic
│       └── display.py    # Same display helper
├── main.py               # Root entry point (placeholder)
└── pyproject.toml
```

## Modules

### providers.py

Manages the registry of LLM providers and abstracts API differences.

**Provider dataclass fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Display name (e.g. "GPT-5-mini") |
| `model` | `str` | Model identifier sent to the API |
| `kind` | `str` | API protocol: `"openai"` or `"anthropic"` |
| `env_var` | `str` | Environment variable holding the API key |
| `prefix_len` | `int` | Characters of the key to print for validation |
| `optional` | `bool` | Whether the provider can be skipped if no key is set |
| `base_url` | `str \| None` | Custom API endpoint (for Gemini, DeepSeek, Groq, Ollama) |
| `api_key_value` | `str \| None` | Hardcoded key (used for Ollama's dummy key) |
| `max_tokens` | `int` | Max response tokens (default: 1000) |

**Configured providers:**

| Name | Model | API Type | Endpoint |
|------|-------|----------|----------|
| GPT-5-mini | gpt-5-mini | OpenAI | Default OpenAI |
| GPT-5-nano | gpt-5-nano | OpenAI | Default OpenAI |
| Claude Sonnet 4.5 | claude-sonnet-4-5 | Anthropic | Default Anthropic |
| Gemini 2.5 Flash | gemini-2.5-flash | OpenAI | Google generativelanguage API |
| DeepSeek Chat | deepseek-chat | OpenAI | DeepSeek API |
| Groq GPT-OSS-120B | openai/gpt-oss-120b | OpenAI | Groq API |
| Ollama Llama 3.2 | llama3.2 | OpenAI | localhost:11434 |

**Key functions:**

- `validate_api_keys()` — prints key status for each provider
- `query_provider(provider, question)` — sends a question to a provider, returns the answer string or `None` if no key is available. Routes to the Anthropic or OpenAI client based on `provider.kind`.

### judge.py

Implements multi-judge ranking where each provider evaluates all answers.

**Key functions:**

- `build_judge_prompt(question, competitors, answers)` — constructs a prompt asking the judge to rank all responses as a JSON object
- `extract_json(text)` — extracts JSON from responses that may include markdown fences or surrounding prose
- `parse_ranking(response_text, competitors)` — parses JSON `{"results": [3, 1, 2]}` into `[(1, "name"), (2, "name"), ...]` tuples
- `judge_answers(provider, question, competitors, answers)` — has a single provider judge all answers
- `average_rankings(all_rankings, competitors)` — averages rank scores across all judges
- `judge_all(question, competitors, answers, judges)` — runs all judges concurrently via `asyncio.gather`, returns per-judge rankings and the averaged leaderboard

### main.py (lab2)

Orchestrates the auto-generated question arena flow:

1. Validate API keys
2. Generate a challenging question via GPT-4o-mini
3. Filter providers to those with available keys
4. Query all available providers concurrently (`asyncio.gather`)
5. Collect successful responses (skip failures)
6. If fewer than 2 competitors responded, abort
7. Run multi-judge ranking concurrently
8. Display per-judge rankings and the final averaged leaderboard

### main.py (desilvaware/best_answer)

Extends the arena with interactive question input:

1. Validate API keys
2. Prompt the user for a question
3. Clarify the question iteratively (up to 5 rounds):
   - GPT-4o-mini evaluates if the question is clear
   - If not clear, it asks clarifying questions
   - User provides answers
   - GPT-4o-mini refines the question
   - Repeat until "CLEAR" or max rounds reached
4. Steps 3-8 from lab2 (query all, judge, leaderboard)

## Data Flow

```
User Question (or auto-generated)
        │
        ▼
┌─────────────────────────────────────────┐
│  Concurrent Provider Queries            │
│  (asyncio.gather + asyncio.to_thread)   │
│                                         │
│  Provider 1 ──► Answer 1                │
│  Provider 2 ──► Answer 2                │
│  Provider 3 ──► Answer 3                │
│  ...                                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Concurrent Judging                     │
│  (each answering provider judges all)   │
│                                         │
│  Judge 1 ──► {"results": [2, 3, 1]}     │
│  Judge 2 ──► {"results": [1, 3, 2]}     │
│  Judge 3 ──► {"results": [1, 2, 3]}     │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Averaging                              │
│  Rank per provider averaged across      │
│  all judges, sorted best-first          │
│                                         │
│  1. Provider 1 (avg rank: 1.33)         │
│  2. Provider 3 (avg rank: 2.00)         │
│  3. Provider 2 (avg rank: 2.67)         │
└─────────────────────────────────────────┘
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `openai` | OpenAI and OpenAI-compatible API client |
| `anthropic` | Anthropic API client |
| `langchain` | LLM orchestration framework |
| `rich` | Formatted markdown console output |
| `python-dotenv` | Load API keys from `.env` |
| `requests` | HTTP requests |
| `pyppeteer` | Browser automation (installed, not yet used) |

**Dev dependencies:** `black` (code formatter)

## Configuration

All configuration is via environment variables loaded from `.env`:

| Variable | Required | Used by |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes | GPT-5-mini, GPT-5-nano, question generation |
| `ANTHROPIC_API_KEY` | No | Claude Sonnet 4.5 |
| `GOOGLE_API_KEY` | No | Gemini 2.5 Flash |
| `DEEPSEEK_API_KEY` | No | DeepSeek Chat |
| `GROQ_API_KEY` | No | Groq GPT-OSS-120B |

Ollama requires no API key but needs a local Ollama server running on port 11434.

## Running

```bash
# Install dependencies
uv sync

# Run the auto-generated question arena
uv run python 1_foundations/lab2/main.py

# Run the interactive arena with question clarification
uv run python desilvaware/best_answer/main.py
```

## Key Design Decisions

- **Every competitor judges** — avoids single-judge bias by averaging rankings across all responding providers
- **OpenAI-compatible abstraction** — providers like Gemini, DeepSeek, Groq, and Ollama all use the OpenAI client with custom `base_url`, so only two code paths are needed (OpenAI vs Anthropic)
- **Graceful degradation** — missing API keys cause providers to be skipped, not crash the program
- **Concurrent execution** — `asyncio.gather` with `asyncio.to_thread` wraps synchronous API calls for concurrent I/O
- **JSON extraction** — regex-based extraction handles judges that wrap their JSON in markdown fences or prose
