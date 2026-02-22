# LLM Agents

A Python project for building LLM-powered agents and an arena that benchmarks multiple LLM providers by having them compete and judge each other's responses.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

## Installing uv

### macOS (Homebrew)
```bash
brew install uv
```

### macOS/Linux (curl)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Project Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd llm_agents
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your-openai-key        # Required
   ANTHROPIC_API_KEY=your-anthropic-key   # Optional
   GOOGLE_API_KEY=your-google-key         # Optional
   DEEPSEEK_API_KEY=your-deepseek-key     # Optional
   GROQ_API_KEY=your-groq-key             # Optional
   ```

## Running

### LLM Arena — Gradio Web UI
```bash
uv run python desilvaware/best_answer/app.py
```
Opens at `http://127.0.0.1:7860` with chat-based question clarification, concurrent provider querying, multi-judge ranking, and a final leaderboard.

### LLM Arena — CLI
```bash
uv run python desilvaware/best_answer/main.py
```
Interactive terminal version with the same clarification and arena flow.

### Foundation Labs
```bash
uv run python 1_foundations/lab1/start.py   # Basic OpenAI interaction
uv run python 1_foundations/lab2/main.py    # Auto-generated question arena
```

### Tests
```bash
uv run pytest                  # Run all tests
uv run pytest -v               # Verbose output
uv run pytest --cov=arena      # With coverage
```

## Architecture

```
                         ┌─────────────────────┐
                         │     User Question    │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            ┌───────▼───────┐              ┌───────▼───────┐
            │  Gradio UI    │              │     CLI       │
            │  (app.py)     │              │  (main.py)    │
            └───────┬───────┘              └───────┬───────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │     Question Clarification     │
                    │  (GPT iterative refinement)    │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │    Concurrent Provider Query   │
                    │   asyncio.gather + to_thread   │
                    └───────────────┬───────────────┘
                                    │
            ┌───────────┬───────────┼───────────┬───────────┐
            ▼           ▼           ▼           ▼           ▼
        ┌───────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌───────┐
        │GPT-5.2│  │GPT-5   │  │Claude  │  │Gemini  │  │ +More │
        │       │  │ -mini  │  │Opus 4.6│  │3.0Flash│  │       │
        └───┬───┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬───┘
            │          │           │            │           │
            └──────────┴───────┬───┴────────────┴───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Concurrent Judging   │
                    │  (each provider ranks │
                    │   all other answers)  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Average Rankings     │
                    │  → Final Leaderboard  │
                    └──────────────────────┘
```

### Key components

| Component | File | Purpose |
|-----------|------|---------|
| Gradio Web UI | `desilvaware/best_answer/app.py` | Interactive web interface with clarification chat, provider status, response timing, question history |
| CLI | `desilvaware/best_answer/main.py` | Terminal-based arena with Rich markdown output |
| Provider config | `arena/config.py` | Default provider list, clarification model, constants |
| Provider abstraction | `arena/providers.py` | `Provider` dataclass, `query_provider()`, cached API clients |
| Judging engine | `arena/judge.py` | Prompt construction, JSON extraction, ranking, averaging |
| Display | `arena/display.py` | Rich console markdown rendering |
| Lab 1 | `1_foundations/lab1/start.py` | Basic OpenAI interaction patterns |
| Lab 2 | `1_foundations/lab2/main.py` | Auto-generated question arena (no clarification) |
| Tests | `tests/test_providers.py`, `tests/test_judge.py` | 47 tests covering providers and judging logic |

## Project Structure

```
llm_agents/
├── arena/                      # Shared library — providers, judging, display
│   ├── config.py               # Default providers list and constants
│   ├── providers.py            # Provider dataclass, query logic, client caching
│   ├── judge.py                # Multi-judge ranking and averaging
│   └── display.py              # Rich markdown console output
├── desilvaware/best_answer/    # LLM Arena application
│   ├── app.py                  # Gradio web UI entry point
│   └── main.py                 # CLI entry point
├── 1_foundations/              # Learning labs
│   ├── lab1/                   # Basic OpenAI interaction patterns
│   └── lab2/                   # Auto-generated question arena
├── tests/                      # pytest test suite for arena/
├── .env.example                # API key template
├── pyproject.toml              # Project config and dependencies
└── CLAUDE.md                   # Claude Code project instructions
```

## Build & Validate

Run these before every commit to ensure nothing is broken:

```bash
uv run ruff check .       # Lint — must pass with no errors
uv run pytest             # Tests — all 47 must pass
```

Both commands must exit cleanly. The CI pipeline (if configured) will run the same checks.

To rebuild the installed package after changing `arena/` or `desilvaware/`:

```bash
uv sync                   # Reinstalls the editable package
```

## Common uv Commands

| Command | Description |
|---------|-------------|
| `uv sync` | Install dependencies from lock file |
| `uv add <package>` | Add a new dependency |
| `uv remove <package>` | Remove a dependency |
| `uv lock` | Update the lock file |
| `uv run <command>` | Run a command in the virtual environment |
| `uv pip list` | List installed packages |
