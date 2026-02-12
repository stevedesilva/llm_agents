# Lab 2 — LLM Arena

An LLM arena that generates a challenging question, sends it to multiple LLM providers, and uses a judge model to rank their answers.

## How It Works

1. **Generate** — OpenAI (`gpt-4o-mini`) creates a challenging question.
2. **Query** — The question is sent to every configured provider in turn.
3. **Judge** — A judge model (`gpt-5-mini`) ranks the responses and prints the results.

## File Structure

```
lab2/
├── main.py        # Entry point — orchestrates question generation, querying, and judging
├── providers.py   # Provider dataclass, provider list, API-key validation, and query logic
├── judge.py       # Builds the judging prompt and calls the judge model to rank answers
└── display.py     # Rich-based markdown console output helper
```

### main.py

| Symbol              | Description                                                        |
|---------------------|--------------------------------------------------------------------|
| `generate_question` | Uses OpenAI to produce a single challenging question for the arena |
| `main`              | Orchestrates the full pipeline: validate keys, generate question, query providers, judge, and display rankings |

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
| `judge_answers`       | Calls the judge model, parses the JSON ranking, and returns a list of `(rank, name)` tuples |

### display.py

| Symbol    | Description                                          |
|-----------|------------------------------------------------------|
| `display` | Renders a markdown string to the terminal using Rich |

## Running

```bash
uv run python main.py
```

Requires at least `OPENAI_API_KEY` in a `.env` file. Other provider keys are optional.
