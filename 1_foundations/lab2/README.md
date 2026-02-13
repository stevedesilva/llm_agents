# Lab 2 — LLM Arena

An LLM arena that generates a challenging question, sends it to multiple LLM providers, and has every provider judge all answers. Individual rankings are averaged into a final result.

## How It Works

1. **Generate** — OpenAI (`gpt-4o-mini`) creates a challenging question.
2. **Query** — All configured providers are queried **concurrently** using `asyncio.gather`.
3. **Judge** — Every provider that answered also serves as a judge, ranking all responses **concurrently**. Individual rankings are averaged to produce a final leaderboard.

## File Structure

```
lab2/
├── main.py        # Entry point — orchestrates question generation, querying, and judging
├── providers.py   # Provider dataclass, provider list, API-key validation, and query logic
├── judge.py       # Multi-judge logic: each provider judges, results are averaged
└── display.py     # Rich-based markdown console output helper
```

### main.py

| Symbol              | Description                                                        |
|---------------------|--------------------------------------------------------------------|
| `generate_question` | Uses OpenAI to produce a single challenging question for the arena |
| `has_api_key`       | Checks whether a provider's API key is available without making an API call |
| `main`              | Async entry point — queries providers and runs judging concurrently via `asyncio.gather` |

### providers.py

| Symbol              | Description                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| `Provider`          | Dataclass holding a provider's name, model, API kind, auth details, and endpoint |
| `PROVIDERS`         | Pre-configured list of providers (GPT-5-mini, GPT-5-nano, Claude Sonnet 4.5, Gemini 2.5 Flash, DeepSeek, Groq, Ollama) |
| `validate_api_keys` | Prints the status of each required API key at startup                       |
| `query_provider`    | Sends a question to a provider and returns the answer (or `None` if the key is missing) |

### judge.py

| Symbol               | Description                                                        |
|-----------------------|--------------------------------------------------------------------|
| `build_judge_prompt`  | Assembles the full judging prompt with the question and all competitor responses |
| `parse_ranking`       | Parses a judge's JSON response into `(rank, name)` tuples |
| `judge_answers`       | Has a single provider judge all answers and return ranked results |
| `average_rankings`    | Averages rank scores across all judges and returns sorted results |
| `judge_all`           | Async — runs all judges concurrently, collects per-judge rankings, and computes averaged final ranking |

### display.py

| Symbol    | Description                                          |
|-----------|------------------------------------------------------|
| `display` | Renders a markdown string to the terminal using Rich |

## Running

```bash
uv run python main.py
```

Requires at least `OPENAI_API_KEY` in a `.env` file. Other provider keys are optional.
