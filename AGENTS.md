# AGENTS Guide

## Commands
- Install: `uv sync --dev`
- Quality: `uv run ruff check --fix && uv run ruff format && uv run mypy && uv run pytest`
- Single test: `uv run pytest tests/unit/test_file.py::TestClass::test_method -v`
- Pre-commit: `uv run pre-commit run --all-files`

## Style
- 4 spaces, 88 chars, double quotes
- Module-only imports: `import pathlib`, not `from pathlib import Path`
- Type hints: `list[str]`, `dict[str, Any]`, annotate all public APIs
- Naming: `snake_case`, `PascalCase`, `UPPER_SNAKE_CASE`
- Error handling: specific exceptions, custom Error classes
- Tests: mirror src structure, descriptive names, fixtures
- Logging: loguru with context
- Docstrings: Google style with Args/Returns/Raises
