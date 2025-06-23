# Ca-Bhfuil AI Code Style Guide

> **Condensed style guide for AI assistants working on Ca-Bhfuil**
>
> **Last Updated**: 2025-01-23 (Sync with docs/code-style.md - added explicit import preference)
>
> **CRITICAL**: This file must stay synchronized with `docs/code-style.md`. When the full guide changes, update this AI-optimized version immediately.

## Core Rules

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

## Testing Patterns

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

### Mocking
```python
@mock.patch("module.external_dependency", autospec=True)
def test_with_mock(self, mock_dep):
    """Test with external dependency mocked."""
    mock_dep.return_value = expected_result
    # Test implementation
    mock_dep.assert_called_once_with(expected_args)
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

1. **Ruff clean**: `uv run ruff check src/ tests/`
2. **Format applied**: `uv run ruff format src/ tests/`
3. **Types check**: `uv run mypy src/`
4. **Tests pass**: `uv run pytest`
5. **Documentation updated**: If public API changed

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
- When `docs/code-style.md` is updated, immediately update this file
- Focus on patterns most critical for AI code generation
- Emphasize anti-patterns that AI assistants commonly make
- Keep examples actionable and immediately usable

**Key Differences from Full Guide**:
- Condensed format for quick reference during coding
- Emphasis on import patterns (most critical for AI)
- Focus on modern Python syntax requirements
- Quick anti-pattern reference

**Key Principle**: Write code that is easy for both humans and AI to understand and maintain.

**Last Updated**: 2025-01-23 - Enhanced with function design patterns, resource management, sync process, and explicit "from package import module" preference
