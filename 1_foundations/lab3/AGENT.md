# AGENT.md

## Lab purpose
- Read a local PDF CV and print extracted text to stdout.

## Entry point
- `main.py`

## Run
- From repo root: `uv run python 1_foundations/lab3/main.py`

## Inputs and dependencies
- Input PDF path is hardcoded: `1_foundations/lab3/me/Steve_deSilva_CV.pdf`.
- Requires `pypdf`.

## Current behavior notes
- `.env` is loaded, but API keys are not used in current logic.
- `OpenAI` and `gradio` are imported but unused.
