# LLM Arena

An LLM arena that clarifies your question, sends it to multiple LLM providers concurrently, and has every provider judge all answers. Individual rankings are averaged into a final leaderboard.

## How It Works

1. **Clarify** — The clarification model iteratively refines your question until it is clear and specific.
2. **Query** — All configured providers are queried **concurrently** using `asyncio.gather`.
3. **Judge** — Every provider that answered also serves as a judge, ranking all responses **concurrently**. Individual rankings are averaged to produce a final leaderboard.

## Running

### Gradio Web UI

```bash
uv run python desilvaware/best_answer/app.py
```

Opens at `http://127.0.0.1:7860`. Features:

- Provider status bar showing which API keys are configured
- Chat-based question clarification before running the arena
- Collapsible answers with per-provider response timing
- Detailed error reasons (timeout, auth failure, etc.)
- Question history dropdown to re-run previous questions
- "New Question" button to reset and start over

### CLI

```bash
uv run python desilvaware/best_answer/main.py
```

Interactive terminal version with Rich markdown output.

### Prerequisites

Requires at least `OPENAI_API_KEY` in a `.env` file. Other provider keys are optional — see `.env.example`.

## File Structure

```
desilvaware/best_answer/
├── app.py         # Gradio web UI entry point
├── main.py        # CLI entry point
└── README.md

arena/              # Shared library (used by both entry points)
├── __init__.py
├── config.py      # Default providers list and shared constants
├── providers.py   # Provider dataclass, query logic, API client caching
├── judge.py       # Multi-judge logic: each provider judges, results are averaged
└── display.py     # Rich-based markdown console output helper
```

## Key Modules

### arena/config.py

| Symbol                     | Description                                              |
|----------------------------|----------------------------------------------------------|
| `DEFAULT_PROVIDERS`        | Pre-configured list of 6 providers (GPT-5.2, GPT-5-mini, Claude Opus 4.6, Gemini 3.0 Flash, DeepSeek, Groq) |
| `CLARIFICATION_MODEL`     | Model used for question clarity checking and refinement  |
| `MAX_CLARIFICATION_ROUNDS` | Maximum clarification iterations before proceeding       |
| `MAX_CLARIFY_ANSWER_LENGTH`| Truncation limit for clarifying answers                  |

### arena/providers.py

| Symbol              | Description                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| `Provider`          | Dataclass holding a provider's name, model, API kind, auth details, and endpoint |
| `validate_api_keys` | Prints the status of each required API key at startup                       |
| `query_provider`    | Sends a question to a provider and returns the answer (or `None` if the key is missing) |

### arena/judge.py

| Symbol               | Description                                                        |
|-----------------------|--------------------------------------------------------------------|
| `build_judge_prompt`  | Assembles the full judging prompt with the question and all competitor responses |
| `extract_json`        | Extracts a JSON object from text that may contain markdown fences or surrounding prose |
| `parse_ranking`       | Parses a judge's JSON response into `(rank, name)` tuples |
| `judge_answers`       | Has a single provider judge all answers and return ranked results |
| `average_rankings`    | Averages rank scores across all judges and returns sorted results |
| `judge_all`           | Async — runs all judges concurrently, collects per-judge rankings, and computes averaged final ranking |
