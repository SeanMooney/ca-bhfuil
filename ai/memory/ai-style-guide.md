# Ca-Bhfuil AI Code Style Guide

> **Condensed style guide for AI assistants working on Ca-Bhfuil**
>
> **Last Updated**: 2025-01-23 (Sync with docs/contributor/code-style.md - added explicit import preference)
>
> **CRITICAL**: This file must stay synchronized with `docs/contributor/code-style.md`. When the full guide changes, update this AI-optimized version immediately.

## Core Rules

### Testing Organization (CRITICAL)
- **Tests MUST be in `tests/` directory, NEVER in `src/`**
- **NO testing utilities in production code** - use proper production interfaces
- **Unit tests**: `tests/unit/`
- **Integration tests**: `tests/integration/`
- **Test fixtures**: `tests/fixtures/`
- **Anti-pattern**: `src/ca_bhfuil/testing/` or similar testing directories in `src/`

### Formatting (Handled by Ruff)
- **Line length**: 88 characters max
- **Indentation**: 4 spaces, never tabs
- **Quotes**: Double quotes (`"`) for strings
- **Imports**: Module-only imports, one per line, sorted by Ruff (stdlib → third-party → local)

### Naming (Manual Enforcement)
- **Variables/functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Single underscore prefix `_private`

### Type Hints (Required)
- Use modern syntax: `list[str]` not `List[str]`
- Type all public functions/methods
- Use `| None` instead of `Optional`
- Use `Any` sparingly with explanation

```python
# Good
def process_repos(urls: list[str]) -> dict[str, CloneResult]:
def get_commit(sha: str) -> pygit2.Commit | None:

# Avoid  
def process_repos(urls: List[str]) -> Dict[str, CloneResult]:
def get_commit(sha: str) -> Optional[pygit2.Commit]:
```

## Documentation Standards

### Docstrings (Required for Public APIs)
Use Google style with sections as needed:

```python
def function_name(param: type) -> return_type:
    """One-line summary in imperative mood.

    Args:
        param: Parameter description.

    Returns:
        Description of return value.

    Raises:
        ExceptionType: When this exception is raised.
    """
```

### Comments
- Explain **why**, not what
- Use for complex business logic
- Avoid obvious comments

## Error Handling Patterns

### Exceptions
```python
# Good - Specific exceptions
try:
    repository = pygit2.Repository(path)
except pygit2.GitError as e:
    logger.error(f"Git error: {e}")
    raise RepositoryError(f"Invalid repository: {path}") from e

# Avoid - Bare except
try:
    repository = pygit2.Repository(path)  
except:
    pass
```

### Custom Exceptions
```python
class CaBhfuilError(Exception):
    """Base exception."""

class ConfigurationError(CaBhfuilError):
    """Config errors."""
```

### Logging
```python
# Good - Context and details
logger.info(f"Cloning {url} to {path}")
logger.error(f"Clone failed for {url}: {error}")

# Avoid - No context
logger.info("Cloning repository")
logger.error(str(error))
```

## Function Design

### Structure
```python
def function_name(
    required_param: str,
    *,  # Keyword-only separator
    optional_param: bool = True,
    callback: Callable[[Progress], None] | None = None,
) -> ResultType:
    """Function with proper parameter organization."""
```

### Resource Management (CRITICAL)
```python
# Use context managers for all resource cleanup
with CloneLockManager(repo_path) as lock:
    result = perform_operation()

# File operations - ALWAYS specify encoding
with open(path, encoding="utf-8") as f:
    content = f.read()

# Configuration reading pattern
def read_config_file(path: pathlib.Path) -> dict[str, Any]:
    """Read configuration from file."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
```

## Testing Philosophy

### Unit vs Integration Tests (CRITICAL)

**Unit Tests (`tests/unit/`)**:
- **Purpose**: Fast, isolated testing of individual components
- **Mocking**: Heavy mocking of external dependencies is **ENCOURAGED**
- **Scope**: Single class/function, isolated from filesystem, network, database
- **Speed**: Must be fast (<100ms per test)
- **Dependencies**: Mock all external systems (git, database, filesystem, network)

**Integration Tests (`tests/integration/`)**:
- **Purpose**: End-to-end testing of real system interactions
- **Mocking**: Minimal mocking - use real systems **PREFERRED**
- **Scope**: Multiple components working together
- **Speed**: Can be slower (1-10s per test)
- **Dependencies**: Use real git repositories, temporary databases, actual file operations

### Test Strategy Matrix

| Test Type | Git Operations | Database | Filesystem | Network | Mocking Level |
|-----------|---------------|----------|------------|---------|---------------|
| Unit      | Mock git calls | Mock DB  | Mock paths | Mock HTTP | Heavy (90%+) |
| Integration| Real git repos | Temp DB | Temp dirs | Real/Skip | Light (10%) |

### Unit Test Patterns

```python
class TestGitOperations:
    """Unit tests mock external dependencies."""

    @mock.patch("pygit2.Repository")
    def test_clone_repository(self, mock_repo):
        """Test git clone logic without actual git operations."""
        mock_repo.return_value = mock_repo_instance
        # Test implementation
        mock_repo.assert_called_once()

    @mock.patch("pathlib.Path.exists", return_value=True)
    def test_path_validation(self, mock_exists):
        """Test path validation logic."""
        # Test implementation
```

### Integration Test Patterns

```python
class TestRepositorySync:
    """Integration tests use real systems with proper XDG isolation."""

    @pytest.mark.asyncio
    async def test_repo_sync_workflow(self, integration_test_environment):
        """Test full sync workflow with real git repository."""
        env = integration_test_environment()

        with env["xdg_context"] as xdg_dirs:
            test_repo = env["test_repo"]

            # Create repository config using file:// protocol
            repo_config = config.RepositoryConfig(
                name="test-repo",
                source={"url": f"file://{test_repo.path}", "type": "git"},
            )

            # Use real database in XDG state directory
            db_manager = SQLModelDatabaseManager(xdg_dirs["state"] / "test.db")
            await db_manager.initialize()

            # Use real config manager with XDG config directory
            config_manager = AsyncConfigManager(xdg_dirs["config"] / "ca-bhfuil")
            await config_manager.generate_default_config()

            # Test with real components
            synchronizer = AsyncRepositorySynchronizer(config_manager, db_manager)
            result = await synchronizer.sync_repository("test-repo")
            assert result.success is True
```

### Environment Isolation for Integration Tests

**CRITICAL**: Use proper XDG fixtures for complete isolation:

```python
# CORRECT: Use fixtures for proper XDG structure
@pytest.fixture
def fake_home_dir():
    """Create fake home directory with proper XDG structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_home = pathlib.Path(tmp_dir)

        # Create proper XDG directory structure
        config_dir = fake_home / ".config"
        cache_dir = fake_home / ".cache"
        state_dir = fake_home / ".local" / "state"

        config_dir.mkdir(parents=True)
        cache_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)

        yield {
            "home": fake_home,
            "config": config_dir,
            "cache": cache_dir,
            "state": state_dir,
        }

@pytest.fixture
def isolated_xdg_environment(fake_home_dir):
    """Set up isolated XDG environment variables."""
    @contextmanager
    def xdg_context():
        with mock.patch.dict(
            "os.environ",
            {
                "XDG_CONFIG_HOME": str(fake_home_dir["config"]),
                "XDG_CACHE_HOME": str(fake_home_dir["cache"]),
                "XDG_STATE_HOME": str(fake_home_dir["state"]),
            },
            clear=False,
        ):
            yield fake_home_dir
    return xdg_context

# Use the fixture in tests
def test_with_isolated_environment(isolated_xdg_environment):
    """Integration test with proper XDG isolation."""
    with isolated_xdg_environment() as xdg_dirs:
        # All config/cache/state operations happen in isolated XDG structure
        config_manager = AsyncConfigManager(xdg_dirs["config"] / "ca-bhfuil")
        # Test operations...
```

**WRONG**: Manual XDG directory setup
```python
# AVOID: Incorrect XDG structure
@mock.patch.dict(
    "os.environ",
    {
        "XDG_CONFIG_HOME": str(tmp_dir / "config"),  # Wrong: should be base dir
        "XDG_CACHE_HOME": str(tmp_dir / "cache"),    # Wrong: should be base dir
        "XDG_STATE_HOME": str(tmp_dir / "state"),    # Wrong: should be base dir
    },
    clear=False,
)
def test_with_incorrect_xdg():
    # This creates wrong directory structure
    pass
```

### Test Structure
```python
class TestFeatureName:
    """Test class for feature."""

    @pytest.fixture
    def setup_data(self):
        """Provide test data."""
        return create_test_data()

    def test_success_case(self, setup_data):
        """Test successful operation."""
        # Test implementation

    def test_error_case(self, setup_data):
        """Test error handling."""
        with pytest.raises(SpecificError, match="expected message"):
            operation_that_fails()
```

### Mocking Guidelines

**Unit Tests - Mock External Dependencies**:
```python
@mock.patch("module.external_dependency", autospec=True)
def test_with_mock(self, mock_dep):
    """Test with external dependency mocked."""
    mock_dep.return_value = expected_result
    # Test implementation
    mock_dep.assert_called_once_with(expected_args)
```

**Integration Tests - Use Real Systems**:
```python
def test_with_real_systems(self):
    """Integration test with minimal mocking."""
    # Use TestRepository fixture for real git operations
    test_repo = TestRepository(tmp_path)
    test_repo.commit("test commit")

    # Use real database
    db = SQLModelDatabaseManager(":memory:")

    # Test actual operations
    result = sync_repository(test_repo.path)
    assert result.success is True
```

## Import Standards (CRITICAL)

### Module/Submodule-Only Imports Required
```python
# CORRECT - Import modules/submodules only, prefer "from package import module"
import os
import pathlib
import typing

import loguru
import pydantic
from rich import console  # PREFERRED over "import rich.console"
from rich import table    # PREFERRED over "import rich.table"

from ca_bhfuil.core import config
from ca_bhfuil.utils import paths

# Usage in code
path = pathlib.Path("/some/path")
logger = loguru.logger
rich_console = console.Console()  # Use imported module
config_manager = config.ConfigManager()

# WRONG - Never import functions/classes directly
from pathlib import Path
from typing import Any, Optional
from ca_bhfuil.core.config import ConfigManager
from rich.console import Console  # Import class directly - WRONG

# WRONG - Never mix import styles
import os
from pathlib import Path  # Don't mix in same group

# WRONG - Never import multiple items
from typing import Any, Optional, Dict
```

### Import Organization (CRITICAL)
**Order with blank lines between groups**:
1. **Standard library**: `import os`, `import pathlib`, `import typing` OR `from collections import abc`
2. **Third-party**: `import loguru`, `import pydantic`, `import pygit2`, `import typer` OR `from rich import console`  
3. **Local**: `from ca_bhfuil.core import config`, `from ca_bhfuil.utils import paths`

**Key Rules (CRITICAL)**:
- **PREFER `from package import module`** over `import package.module` for submodules
- **Examples**: `from rich import console` NOT `import rich.console`
- **Examples**: `from collections import abc` NOT `import collections.abc`
- **Simple modules**: `import os`, `import pathlib` (when they're top-level modules)
- Never use `from typing import List, Dict, Optional` (legacy - use built-in types)
- Never use wildcard imports (`from module import *`)
- Never use relative imports (even within same package)
- One module per line, sorted alphabetically within groups

## Common Patterns

### Configuration Classes
```python
@dataclass
class ConfigClass:
    """Configuration with validation."""
    required_field: str
    optional_field: int = 100

    @property
    def computed_field(self) -> str:
        """Computed property."""
        return f"computed_{self.required_field}"
```

### Progress Tracking
```python
@dataclass
class ProgressInfo:
    """Progress information."""
    completed: int
    total: int
    current_item: str | None = None

    @property
    def percentage(self) -> float:
        """Progress as percentage."""
        return (self.completed / self.total) * 100.0 if self.total > 0 else 0.0
```

### Result Objects
```python
@dataclass
class OperationResult:
    """Operation result."""
    success: bool
    data: Any | None = None
    error: str | None = None
    duration: float = 0.0
```

## Anti-Patterns (Avoid)

### Code Issues
```python
# Avoid - Mutable defaults
def function(items=[]): pass

# Good
def function(items: list[Any] | None = None):
    if items is None:
        items = []

# Avoid - Too many parameters (limit to ~3-4)
def function(a, b, c, d, e, f): pass

# Good - Use dataclass for complex parameters
@dataclass
class ProcessingOptions:
    cache_size: int = 1000
    retry_count: int = 3
    timeout: int = 30

def function(data: str, options: ProcessingOptions | None = None):
    if options is None:
        options = ProcessingOptions()

# Use keyword-only arguments for optional parameters
def clone_repository(
    url: str,
    target_path: pathlib.Path,
    *,  # Keyword-only separator
    bare: bool = True,
    force: bool = False,
) -> CloneResult:
    """Clone repository with specific options."""
    pass
```

### Import Issues
```python
# Avoid
from module import *
from typing import List, Dict, Optional  # Legacy

# Good  
from module import specific_item
# Use built-in types directly
```

### Testing Organization Issues (CRITICAL)
```python
# WRONG - Tests in src/ directory
src/ca_bhfuil/testing/test_utils.py
src/ca_bhfuil/testing/alembic_utils.py

# WRONG - Production code importing from testing
from ca_bhfuil.testing import alembic_utils  # In production code

# CORRECT - Tests in tests/ directory
tests/unit/test_alembic_utils.py
tests/fixtures/alembic.py
tests/integration/test_integration_flow.py

# CORRECT - Production code using production interfaces
from ca_bhfuil.storage import alembic_interface  # In production code
```

## Ruff Auto-Fixes

These are handled automatically:
- Line length formatting
- Import sorting and organization
- Trailing whitespace removal
- Quote style consistency
- Deprecated typing imports (`List` → `list`)

## Manual Review Required

These need human/AI attention:
- Function complexity and length
- Error handling completeness
- Documentation quality
- Test coverage
- Performance implications
- Security considerations

## Commit Format

```
type(scope): description

Detailed explanation if needed.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Quick Checks Before Committing

1. **Auto-fix first**: `uv run ruff check --fix src/ tests/` (fixes most issues automatically)
2. **Format applied**: `uv run ruff format src/ tests/`
3. **Types check**: `uv run mypy src/`
4. **Tests pass**: `uv run pytest`
5. **Documentation updated**: If public API changed

## Automated Tools and What They Fix

### Ruff Auto-Fixes (Use `--fix` flag)
- **Import sorting**: Automatically organizes imports by stdlib → third-party → local
- **Import grouping**: Adds proper spacing between import groups
- **Unused imports**: Removes imports that aren't used
- **F-string conversion**: Converts `.format()` and `%` formatting to f-strings
- **Type annotation updates**: Converts `List[str]` to `list[str]`, `Optional[T]` to `T | None`
- **Pathlib enforcement**: Suggests `pathlib.Path` over `os.path` operations
- **Comprehension optimization**: Converts loops to list/dict comprehensions where appropriate
- **Performance improvements**: Identifies and fixes common performance anti-patterns

### What AI Assistants Should Let Ruff Handle
- **Don't manually sort imports**: Run `ruff check --fix` instead
- **Don't manually convert to f-strings**: Ruff will do this automatically
- **Don't manually fix line lengths**: Ruff format handles this
- **Don't manually update type annotations**: Ruff converts legacy typing automatically

### What Still Requires Manual Attention
- **Function complexity**: Break down large functions
- **Error handling patterns**: Choose appropriate exception types
- **Documentation quality**: Write meaningful docstrings
- **Test coverage**: Ensure comprehensive testing
- **Security considerations**: Review sensitive operations

## Priority Order

When making code changes:

1. **Correctness**: Code works as intended
2. **Safety**: Proper error handling, type safety
3. **Readability**: Clear names, good structure
4. **Performance**: Only optimize when needed
5. **Style**: Consistent with this guide

---

## Synchronization Notes

**AI Assistant Responsibilities**:
- When `docs/contributor/code-style.md` is updated, immediately update this file
- Focus on patterns most critical for AI code generation
- Emphasize anti-patterns that AI assistants commonly make
- Keep examples actionable and immediately usable

**Key Differences from Full Guide**:
- Condensed format for quick reference during coding
- Emphasis on import patterns (most critical for AI)
- Focus on modern Python syntax requirements
- Quick anti-pattern reference

**Key Principle**: Write code that is easy for both humans and AI to understand and maintain.

**Last Updated**: 2025-07-17 - Enhanced with testing philosophy, unit vs integration test patterns, and XDG environment isolation
