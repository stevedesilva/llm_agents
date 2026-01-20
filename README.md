# LLM Agents

A Python project for building LLM-powered agents.

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

### pip
```bash
pip install uv
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
   This creates a virtual environment in `.venv/` and installs all dependencies from `uv.lock`.

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your-openai-key
   ANTHROPIC_API_KEY=your-anthropic-key
   ```

## Usage

Run the main script:
```bash
uv run main.py
```

Run any Python file:
```bash
uv run python <script>.py
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

## Project Structure

```
llm_agents/
├── .venv/           # Virtual environment
├── .env             # Environment variables (not committed)
├── .python-version  # Python version
├── pyproject.toml   # Project configuration
├── uv.lock          # Locked dependencies
├── main.py          # Entry point
└── README.md
```
