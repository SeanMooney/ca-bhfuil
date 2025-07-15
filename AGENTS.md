# AGENTS Guide

## Agent Requirements
- Read CLAUDE.md and follow its requirements

## Commands
- Install dependencies: pip install -r requirements-all.txt
- Lint & format: uv run ruff check --fix && uv run ruff format
- Type check: uv run mypy
- Test all: uv run pytest
- Test single: uv run pytest path/to/test_file.py::TestClass::test_method -v

## Code Style
- Indent with 4 spaces; max line length 88
- Use double quotes for strings; triple double quotes for docstrings
- Imports: module-only, groups stdlib/third-party/local, alphabetize, no relative/wildcard
- Naming: snake_case for functions/vars, PascalCase for classes, UPPER_SNAKE_CASE for constants
- Type hints: use list[str], dict[str, Any]; annotate all public APIs
- Error handling: catch specific exceptions; no bare except; use custom Exception subclasses
- Docstrings: Google style with Args, Returns, Raises sections
- Tests: mirror source in tests/, use fixtures, descriptive names
- Logging: use loguru; include context; proper log levels
- Exceptions: class names end with Error or Exception