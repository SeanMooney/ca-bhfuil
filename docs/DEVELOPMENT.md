# Development Environment Setup

This document describes how to set up a development environment for Ca-Bhfuil using UV and Python.

## Prerequisites

1. **Python 3.12+** - The minimum supported Python version
2. **UV** - Fast Python package manager
3. **Git** - Version control

### Installing Python

```bash
# On macOS with Homebrew
brew install python@3.12

# On Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# On other systems, use pyenv or your system package manager
```

### Installing UV

```bash
# Install UV (cross-platform)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Or with Homebrew (macOS)
brew install uv
```

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SeanMooney/ca-bhfuil.git
   cd ca-bhfuil
   ```

2. **Set up the development environment:**
   ```bash
   # Install dependencies
   uv sync --dev

   # Set up pre-commit hooks
   uv run pre-commit install
   ```

3. **Start developing:**
   ```bash
   # Run tests
   uv run pytest

   # Lint code
   uv run ruff check

   # Type check
   uv run mypy

   # Run the CLI
   uv run ca-bhfuil --help
   ```

## Development Environment Features

The development setup provides:

### System Requirements
- **Python 3.12+** - Primary development language
- **UV** - Fast Python package manager and environment management
- **libgit2** - Required for pygit2 (git operations)
- **Git** - Version control
- **Pre-commit** - Git hooks for code quality

### Python Environment
- Virtual environment managed by UV
- All project and dev dependencies installed
- Development tools (pytest, ruff, mypy) configured
- Consistent development environment across machines

### Manual Setup Steps
- Install dependencies with `uv sync --dev`
- Set up pre-commit hooks with `uv run pre-commit install`
- Run quality checks before committing

## System Dependencies

### Installing libgit2

The project requires libgit2 for git operations via pygit2:

```bash
# On macOS with Homebrew
brew install libgit2

# On Ubuntu/Debian
sudo apt update
sudo apt install libgit2-dev

# On CentOS/RHEL/Fedora
sudo dnf install libgit2-devel  # or yum install libgit2-devel
```

## Environment Variables

You can optionally set these variables for development:

```bash
export CA_BHFUIL_ENV=development     # Environment indicator
export PYTHONDONTWRITEBYTECODE=1     # Prevent .pyc files
export PYTHONUNBUFFERED=1            # Immediate stdout/stderr
```

Or create a `.env` file in the project root:
```bash
CA_BHFUIL_ENV=development
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
```

## Common Commands

```bash
# Install/update dependencies
uv sync

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_cli.py

# Run with coverage
uv run pytest --cov=ca_bhfuil

# Lint code
uv run ruff check

# Format code
uv run ruff format

# Type check
uv run mypy

# Run pre-commit on all files
pre-commit run --all-files

# Build package
uv build

# Run CLI locally
uv run ca-bhfuil --help
```

## Container Development

The project includes Docker containers for both production and development use.

### Building Containers

Use the provided build script:

```bash
# Build production container
./scripts/build-container.sh

# Build development container
./scripts/build-container.sh --dev

# Build with custom tag
./scripts/build-container.sh --tag v0.1.0
```

Or build manually:

```bash
# Production container (minimal, optimized)
docker build -t ca-bhfuil:latest .

# Development container (with full tooling)
docker build -f Dockerfile.dev -t ca-bhfuil:dev .
```

### Running Containers

**Production container:**
```bash
# Run CLI
docker run --rm ca-bhfuil:latest --help

# Mount configuration directory
docker run --rm \
  -v ~/.config/ca-bhfuil:/home/ca-bhfuil/.config/ca-bhfuil \
  ca-bhfuil:latest <command>
```

**Development container:**
```bash
# Interactive development
docker run -it --rm \
  -v $(pwd):/app \
  ca-bhfuil:dev bash

# Run tests in container
docker run --rm \
  -v $(pwd):/app \
  ca-bhfuil:dev \
  uv run pytest
```

### Using Docker Compose

The project includes docker-compose.yml for easier container management:

```bash
# Build and run production container
docker-compose --profile manual run ca-bhfuil --help

# Build and run development container
docker-compose --profile dev run ca-bhfuil-dev

# Run tests in development container
docker-compose --profile dev run ca-bhfuil-dev uv run pytest
```

## Troubleshooting

### System Dependencies Issues

1. **libgit2 not found**: Ensure libgit2 is installed and in your system PATH
2. **SSL certificate errors**: Make sure ca-certificates are installed on your system
3. **Compilation errors**: Ensure you have build tools installed (gcc, make, etc.)

### Python Issues

1. **Import errors**: Ensure you're using `uv run` or activate the virtual environment
2. **Package not found**: Run `uv sync --dev` to ensure all dependencies are installed
3. **Version conflicts**: Delete `.venv` and run `uv sync --dev` again

### UV Issues

1. **UV command not found**: Ensure UV is installed and in your PATH
2. **Virtual environment issues**: Delete `.venv` and run `uv sync --dev` to recreate
3. **Lock file conflicts**: Run `uv lock --upgrade` to regenerate uv.lock

## IDE Integration

### VS Code

The UV environment works well with VS Code. Recommended extensions:

- Python
- Pylance  
- Ruff
- MyPy

Configure VS Code to use the UV virtual environment:
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python"
}
```

### Other IDEs

Most IDEs will work with UV virtual environments. Point your IDE to the Python interpreter at `.venv/bin/python` (or `.venv/Scripts/python.exe` on Windows).

## Contributing

1. Fork the repository
2. Set up the development environment using this guide
3. Create a feature branch
4. Make your changes with proper tests
5. Ensure all quality checks pass (`pre-commit run --all-files`)
6. Submit a pull request

---

For more information, see the [project documentation](../README.md) and [AI development guide](../CLAUDE.md).
