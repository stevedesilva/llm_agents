# Lab 2 — LLM Arena (Auto-Generated Questions)

An LLM arena that auto-generates a challenging question, sends it to multiple providers concurrently, and has every provider judge all answers. Individual rankings are averaged into a final leaderboard.

## How It Works

1. **Generate** — GPT-4o-mini creates a challenging question automatically.
2. **Query** — All configured providers are queried **concurrently** using `asyncio.gather`.
3. **Judge** — Every provider that answered also serves as a judge, ranking all responses **concurrently**. Individual rankings are averaged to produce a final leaderboard.

## File Structure

```
lab2/
└── main.py        # Entry point — generates question, queries providers, runs judging
```

Core logic (Provider, judging, display) lives in the shared `arena/` package at the project root.

### main.py

| Symbol              | Description                                                        |
|---------------------|--------------------------------------------------------------------|
| `PROVIDERS`         | Local provider list (GPT-5-mini, GPT-5-nano, Claude Sonnet 4.5, Gemini 2.5 Flash, DeepSeek, Groq, Ollama) |
| `generate_question` | Uses GPT-4o-mini to produce a challenging question for the arena   |
| `main`              | Async entry point — queries providers and runs judging concurrently |

## Running

```bash
uv run python 1_foundations/lab2/main.py
```

Requires at least `OPENAI_API_KEY` in a `.env` file. Other provider keys are optional. Ollama requires a local server on port 11434.

## Differences from desilvaware/best_answer/

This lab auto-generates questions (no user input or clarification step). The `desilvaware/best_answer/` version adds interactive question clarification and a Gradio web UI.
