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

## Async Development Patterns

Ca-Bhfuil uses async/await patterns throughout the codebase for concurrent operations and non-blocking I/O. This section covers async development patterns and best practices.

### Async Architecture Overview

The project follows an async-first architecture with these key components:

- **Async I/O Layer**: File operations, database access, and HTTP requests
- **Thread Pool Wrappers**: For synchronous pygit2 operations
- **Progress Tracking**: Real-time progress reporting across async boundaries
- **CLI Bridge**: Async-to-sync integration for Typer commands

### Async Development Setup

#### Required Dependencies

The async infrastructure requires these dependencies (already included):

```toml
# Core async dependencies
aiofiles = ">=23.0.0"      # Async file operations
aiosqlite = ">=0.19.0"     # Async SQLite operations
watchfiles = ">=0.21.0"    # Async file watching
pytest-asyncio = ">=0.21.0" # Async testing support
```

#### Async Testing Configuration

The project is configured for async testing with pytest-asyncio:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Async Development Patterns

#### 1. Async Function Definition

```python
import asyncio
from typing import Any

async def async_operation() -> Any:
    """Define async functions with proper type hints."""
    await asyncio.sleep(0.1)  # Simulate async work
    return "result"
```

#### 2. Async Context Managers

```python
from ca_bhfuil.integrations import async_http

async def http_operations():
    """Use async context managers for resource management."""
    async with async_http.AsyncHTTPClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()
```

#### 3. Concurrent Operations

```python
from ca_bhfuil.core import async_repository

async def concurrent_operations():
    """Run multiple operations concurrently."""
    repo_manager = async_repository.AsyncRepositoryManager()

    tasks = [
        clone_repository("https://github.com/user/repo1"),
        clone_repository("https://github.com/user/repo2"),
        analyze_repository("/path/to/repo3")
    ]

    results = await repo_manager.run_concurrently(tasks)
    return results
```

#### 4. Progress Reporting

```python
from ca_bhfuil.core.models import progress

async def operation_with_progress(progress_callback=None):
    """Report progress during long operations."""
    total_steps = 100

    for i in range(total_steps):
        # Do work
        await asyncio.sleep(0.01)

        if progress_callback:
            await progress_callback(
                progress.OperationProgress(
                    total=total_steps,
                    completed=i + 1,
                    status=f"Processing step {i + 1}"
                )
            )
```

#### 5. Error Handling

```python
from ca_bhfuil.core import async_errors

async def resilient_operation():
    """Handle errors with retry logic."""
    error_handler = async_errors.AsyncErrorHandler(
        attempts=3,
        initial_backoff=1.0
    )

    return await error_handler.retry(
        unreliable_operation(),
        retry_on=(ConnectionError, TimeoutError)
    )
```

### CLI Integration Patterns

#### Async Command Implementation

```python
from ca_bhfuil.cli.async_bridge import async_command, with_progress
import typer

@typer.command()
@async_command
async def clone_repos(
    urls: list[str] = typer.Argument(..., help="Repository URLs")
):
    """Clone multiple repositories with progress display."""

    async def clone_all():
        # Implementation here
        pass

    await with_progress(
        clone_all(),
        "Cloning repositories...",
        show_progress=True
    )
```

#### Progress Display

```python
from ca_bhfuil.cli.async_bridge import with_progress

async def long_operation():
    """Long-running operation with progress display."""
    # Implementation
    pass

# Run with progress bar
result = await with_progress(
    long_operation(),
    "Processing...",
    show_progress=True
)
```

### Testing Async Code

#### Async Test Structure

```python
import pytest
from ca_bhfuil.core import async_config

@pytest.mark.asyncio
async def test_async_config_loading():
    """Test async configuration loading."""
    manager = async_config.AsyncConfigManager()
    config = await manager.load_configuration()
    assert config is not None
```

#### Async Fixtures

```python
import pytest
from ca_bhfuil.core import async_config

@pytest.fixture
async def async_config_manager():
    """Provide async config manager for tests."""
    manager = async_config.AsyncConfigManager()
    yield manager
    # Cleanup if needed
```

#### Mocking Async Operations

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_operation():
    """Test with mocked async operation."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {"data": "test"}

    result = await mock_client.get("/test")
    assert result == {"data": "test"}
```

### Best Practices

#### 1. Resource Management

```python
# Always use async context managers
async with AsyncHTTPClient() as client:
    response = await client.get("https://api.example.com")

# Proper cleanup for thread pools
git_manager = AsyncGitManager()
try:
    # Use git manager
    pass
finally:
    git_manager.shutdown()
```

#### 2. Error Handling

```python
# Use specific exception types
try:
    result = await operation()
except asyncio.TimeoutError:
    raise OperationTimeoutError("Operation timed out")
except ConnectionError:
    raise NetworkError("Network connection failed")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

#### 3. Type Hints

```python
from typing import Any, Awaitable

async def typed_operation() -> str:
    """Use proper type hints for async functions."""
    return "result"

def sync_wrapper() -> Awaitable[str]:
    """Return coroutines from sync functions."""
    return typed_operation()
```

#### 4. Concurrent Operations

```python
# Use semaphores for resource control
semaphore = asyncio.Semaphore(5)

async def controlled_operation():
    async with semaphore:
        # Operation that uses limited resources
        pass

# Run multiple operations
tasks = [controlled_operation() for _ in range(20)]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Common Pitfalls

#### 1. Blocking Operations

```python
# ❌ Don't do this - blocks the event loop
import time

async def bad_operation():
    time.sleep(1)  # Blocks the event loop

# ✅ Do this instead
async def good_operation():
    await asyncio.sleep(1)  # Non-blocking
```

#### 2. Missing await

```python
# ❌ Don't forget await
async def bad_function():
    result = async_operation()  # Missing await
    return result

# ✅ Always await async operations
async def good_function():
    result = await async_operation()
    return result
```

#### 3. Improper Exception Handling

```python
# ❌ Don't catch all exceptions without re-raising
async def bad_error_handling():
    try:
        await operation()
    except Exception as e:
        logger.error(f"Error: {e}")
        # Exception is swallowed

# ✅ Re-raise or handle appropriately
async def good_error_handling():
    try:
        await operation()
    except SpecificError as e:
        logger.error(f"Specific error: {e}")
        raise  # Re-raise to maintain error flow
```

### Performance Considerations

#### 1. Connection Pooling

```python
# Use connection pooling for database operations
db_manager = AsyncDatabaseManager("db.sqlite")
await db_manager.connect(pool_size=10)  # Limit concurrent connections
```

#### 2. Rate Limiting

```python
# Use semaphores for rate limiting
rate_limiter = asyncio.Semaphore(5)  # Max 5 concurrent requests

async def rate_limited_request():
    async with rate_limiter:
        return await make_request()
```

#### 3. Background Tasks

```python
# Use task managers for background operations
task_manager = AsyncTaskManager()
task_id = task_manager.create_task(background_analysis())

# Check status later
status = task_manager.get_status(task_id)
```

### Debugging Async Code

#### 1. Enable asyncio Debug Mode

```bash
# Set environment variable for debugging
export PYTHONASYNCIODEBUG=1
uv run ca-bhfuil --help
```

#### 2. Use asyncio.run() for Testing

```python
# Test async functions in isolation
async def test_function():
    return await async_operation()

result = asyncio.run(test_function())
```

#### 3. Monitor Event Loop

```python
import asyncio

async def debug_operation():
    loop = asyncio.get_running_loop()
    print(f"Event loop: {loop}")
    print(f"Loop running: {loop.is_running()}")
```

### Integration with Existing Code

The async infrastructure is designed to work alongside existing synchronous code:

- **CLI Bridge**: Seamlessly integrates async operations with Typer commands
- **Thread Pool Wrappers**: Handle synchronous pygit2 operations
- **Progress Tracking**: Bridges sync/async boundaries for progress reporting
- **Error Handling**: Maintains consistent error patterns across sync/async code

For more detailed information, see the [Concurrency Architecture](../design/concurrency.md) documentation.

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
