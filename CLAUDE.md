# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM Agents is a Python project for building LLM-powered agents using OpenAI and Anthropic APIs. It uses `uv` as the package manager.

## Build and Run Commands

```bash
# Install dependencies
uv sync

# Run main entry point
uv run main.py

# Run any script
uv run python <script>.py

# Add a dependency
uv add <package>

# Remove a dependency
uv remove <package>
```

## Architecture

The project is organized into numbered folders representing different learning modules:
- `1_foundations/` - Basic LLM interaction patterns (labs for learning fundamentals)

Each lab folder contains standalone scripts demonstrating specific concepts.

## Key Patterns

- Environment variables are loaded from `.env` using `python-dotenv`
- Console output uses `rich` for formatted markdown rendering
- OpenAI client pattern: load API key → create client → call chat completion

## Dependencies

- `openai` / `anthropic` - LLM API clients
- `langchain` - LLM orchestration framework
- `rich` - Terminal formatting
- `python-dotenv` - Environment variable loading
