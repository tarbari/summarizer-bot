# AGENTS.md

## Project overview

A Discord bot that reads message history from a channel and summarizes conversations once a day, specifically designed for news feed channels.

## Setup commands

- Install deps: `uv sync`
- Start bot: `uv run python main.py`
- Add dependency: `uv add <package-name>`

## Code style

- Python code should follow PEP 8 conventions.
- Use type hints where appropriate.
- The project uses `discord-py` and `python-dotenv` dependencies.

## Dependency management

- **Only use `uv add` to add new dependencies** - never manually edit `pyproject.toml`
- Never manually modify the `[project.dependencies]` section in `pyproject.toml`
