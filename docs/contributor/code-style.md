# Ca-Bhfuil Code Style Guide

> **A comprehensive style guide for Python development on the Ca-Bhfuil project**

## Philosophy

This style guide is built on the principle that **code is read more often than it is written**. Our goal is to create code that is:

- **Readable**: Clear and understandable to both humans and AI assistants
- **Consistent**: Following established patterns across the entire codebase
- **Maintainable**: Easy to modify, extend, and debug
- **Professional**: Meeting industry standards for open source Python projects

## Core Principles

### 1. Readability First
- Write code that tells a story
- Use descriptive names over clever abbreviations
- Prefer explicit over implicit when it improves clarity
- Break complex logic into smaller, focused functions

### 2. Consistency Matters
- Follow established patterns within the codebase
- Use automated tools (Ruff, mypy) to enforce consistency
- When in doubt, match the surrounding code style

### 3. Modern Python Practices
- Use Python 3.10+ features appropriately
- Leverage type hints for better code documentation
- Prefer standard library solutions when available
- Use context managers for resource management

## Code Formatting

### Line Length and Wrapping
- **Maximum line length**: 88 characters (Ruff/Black standard)
- Use implicit line continuation within parentheses, brackets, and braces
- Break long parameter lists and method calls using parentheses

```python
# Good
result = some_function(
    parameter_one="value1",
    parameter_two="value2",
    parameter_three="value3",
)

# Good - fits within line limit
short_result = some_function(param1, param2)

# Avoid - line too long
very_long_result = some_function(parameter_one="value1", parameter_two="value2", parameter_three="value3")
```

### Indentation
- Use **4 spaces** for indentation (never tabs)
- Be consistent with indentation levels
- Align continuation lines appropriately

### Blank Lines
- **Two blank lines** between top-level class and function definitions
- **One blank line** between method definitions within a class
- Use blank lines sparingly within functions to separate logical sections

### Quotes
- Use **double quotes** for strings consistently
- Use single quotes only when the string contains double quotes
- Use triple double quotes for docstrings

```python
# Good
message = "Hello, world!"
sql_query = 'SELECT * FROM table WHERE name = "value"'

# Avoid mixing unnecessarily
message = 'Hello, world!'  # Inconsistent with project standard
```

## Import Organization

Organize imports in the following order with blank lines between groups:

1. **Standard library imports**
2. **Third-party library imports**
3. **Local application imports**

Within each group, sort imports alphabetically. Use absolute imports for clarity.

```python
# Standard library
import os
import pathlib
import sys
import typing
from collections import abc  # PREFERRED: "from package import module"

# Third-party  
import loguru
import pydantic
import pygit2
import typer
from rich import console    # PREFERRED: "from rich import console" NOT "import rich.console"
from rich import table      # PREFERRED: "from rich import table" NOT "import rich.table"

# Local application
from ca_bhfuil.core import config
from ca_bhfuil.utils import paths

# Usage in code:
# path = pathlib.Path("/some/path")
# logger = loguru.logger
# rich_console = console.Console()  # Use imported module
# config_manager = config.ConfigManager()
```

### Import Guidelines
- **PREFER `from package import module` over `import package.module`** - for all submodules and packages
- **Examples**: Use `from rich import console` NOT `import rich.console`
- **Examples**: Use `from collections import abc` NOT `import collections.abc`
- **Simple modules**: Use `import os`, `import pathlib` for top-level modules
- **Never import functions, classes, or constants directly** - only import modules/submodules
- **One module per line** - no comma-separated imports
- **No mixed import styles** - do not mix `import` and `from import` in the same group
- **Use fully qualified names** in code (e.g., `pathlib.Path`, not just `Path`)
- **Never use wildcard imports** (`from module import *`)
- **Never use relative imports**, even for closely related modules within the same package

## Naming Conventions

### Variables and Functions
- Use **snake_case** for variable and function names
- Use descriptive names that explain the purpose
- Avoid single-letter names except for short loops or mathematical expressions

```python
# Good
user_count = len(users)
repository_path = get_repository_path(url)

def calculate_commit_distance(from_commit, to_commit):
    """Calculate the distance between two commits."""
    pass

# Avoid
n = len(users)  # Not descriptive
repoPath = get_repository_path(url)  # Wrong case style
```

### Classes and Exceptions
- Use **PascalCase** for class names
- Use descriptive names that indicate the class purpose
- Exception classes should end with "Error" or "Exception"

```python
# Good
class RepositoryManager:
    """Manages git repository operations."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass

# Avoid
class repoManager:  # Wrong case style
class BadConfig(Exception):  # Not descriptive enough
```

### Constants
- Use **UPPER_SNAKE_CASE** for constants
- Define constants at module level
- Group related constants together

```python
# Good
DEFAULT_CACHE_SIZE = 1000
MAX_RETRY_ATTEMPTS = 3
CONFIG_FILE_NAME = "repositories.yaml"

# Repository storage types
STORAGE_TYPE_BARE = "bare"
STORAGE_TYPE_WORKING = "working"
```

### Private Members
- Use single leading underscore for internal use: `_internal_method()`
- Use double leading underscore only for name mangling: `__private_attribute`
- Prefer single underscore for most "private" usage

## Type Hints and Documentation

### Type Hints
- Use type hints for all public functions and methods
- Use modern type hint syntax (Python 3.10+)
- Be specific with type hints when possible

```python
# Good - Modern syntax
def process_repositories(repos: list[str]) -> dict[str, Any]:
    """Process a list of repository URLs."""
    results: dict[str, Any] = {}
    return results

# Avoid - Legacy typing module
from typing import List, Dict
def process_repositories(repos: List[str]) -> Dict[str, Any]:
    pass

# Good - Specific types
def get_commit_by_sha(sha: str) -> pygit2.Commit | None:
    """Get commit by SHA, return None if not found."""
    pass
```

### Docstrings
Use **Google-style docstrings** for all public modules, classes, and functions:

```python
def clone_repository(
    url: str,
    target_path: Path,
    *,
    bare: bool = True,
    progress_callback: Callable[[CloneProgress], None] | None = None,
) -> CloneResult:
    """Clone a git repository to the specified path.

    Args:
        url: The repository URL to clone from.
        target_path: Local path where repository will be cloned.
        bare: Whether to create a bare repository. Defaults to True.
        progress_callback: Optional callback for progress updates.

    Returns:
        CloneResult containing operation status and metadata.

    Raises:
        CloneError: If the clone operation fails.
        ValidationError: If the URL or path is invalid.

    Examples:
        >>> result = clone_repository(
        ...     "https://github.com/user/repo.git",
        ...     Path("/tmp/repo")
        ... )
        >>> print(f"Cloned {result.objects_count} objects")
    """
    # Implementation here
```

### Docstring Guidelines
- Start with a concise one-line summary
- Use imperative mood ("Clone a repository" not "Clones a repository")
- Include Args, Returns, Raises, and Examples sections as appropriate
- Keep descriptions focused and actionable

## Error Handling

### Exception Handling
- Catch specific exceptions, never use bare `except:`
- Handle exceptions at the appropriate level
- Provide meaningful error messages
- Use custom exceptions for domain-specific errors

```python
# Good
try:
    repository = pygit2.Repository(repo_path)
except pygit2.GitError as e:
    logger.error(f"Failed to open repository at {repo_path}: {e}")
    raise RepositoryError(f"Invalid repository: {repo_path}") from e
except PermissionError as e:
    logger.error(f"Permission denied accessing {repo_path}")
    raise AccessError(f"Cannot access repository: {e}") from e

# Avoid
try:
    repository = pygit2.Repository(repo_path)
except:  # Too broad
    pass  # Silent failure
```

### Custom Exceptions
Define specific exceptions for different error conditions:

```python
class CaBhfuilError(Exception):
    """Base exception for all ca-bhfuil errors."""
    pass

class ConfigurationError(CaBhfuilError):
    """Configuration-related errors."""
    pass

class RepositoryError(CaBhfuilError):
    """Repository operation errors."""
    pass

class CloneError(RepositoryError):
    """Repository cloning errors."""
    pass
```

## Logging

### Logging Practices
- Use structured logging with loguru
- Include relevant context in log messages
- Use appropriate log levels
- Support delayed string interpolation for performance

```python
# Good
logger.info(f"Cloning repository {url} to {target_path}")
logger.debug(f"Clone progress: {progress.objects_progress:.1f}%")
logger.error(f"Clone failed for {url}: {error}")

# Good - With context
logger.bind(repo_url=url, target_path=target_path).info("Starting clone operation")

# Avoid
logger.info("Cloning repository")  # Not enough context
logger.error(str(error))  # No context about what failed
```

### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about program execution
- **WARNING**: Something unexpected happened but operation continues
- **ERROR**: A serious problem occurred; operation failed
- **CRITICAL**: A very serious error occurred; program may abort

## Testing Standards

### Test Organization
- Mirror the source structure in the `tests/` directory
- Use descriptive test class and method names
- Group related tests in classes
- Use fixtures for common test setup

```python
class TestRepositoryCloner:
    """Test repository cloning functionality."""

    @pytest.fixture
    def temp_repo_path(self, tmp_path):
        """Provide a temporary repository path."""
        return tmp_path / "test-repo"

    def test_successful_clone(self, temp_repo_path):
        """Test successful repository cloning."""
        # Test implementation

    def test_clone_with_invalid_url(self, temp_repo_path):
        """Test cloning with invalid URL raises appropriate error."""
        # Test implementation
```

### Test Naming
- Use descriptive names that explain what is being tested
- Start with `test_` prefix
- Include the expected outcome: `test_clone_with_invalid_url_raises_error`

### Mocking Guidelines
- Use `unittest.mock` with `autospec=True` for safety
- Mock at the appropriate level (usually external dependencies)
- Verify both behavior and return values

```python
@mock.patch("ca_bhfuil.core.git.clone.pygit2.clone_repository", autospec=True)
def test_clone_success(self, mock_clone):
    """Test successful clone operation."""
    mock_repo = Mock()
    mock_repo.is_bare = True
    mock_clone.return_value = mock_repo

    # Test implementation
    mock_clone.assert_called_once()
```

### Assertion Guidelines
- Use specific assertion methods when available
- Provide helpful assertion messages for complex conditions
- Test both positive and negative cases

```python
# Good
assert result.success is True
assert result.error is None
assert result.objects_count > 0

# Better with context
assert result.success, f"Clone should succeed but got error: {result.error}"

# Use specific assertions
with pytest.raises(ValidationError, match="Invalid URL format"):
    validate_repository_url("not-a-url")
```

## Code Quality

### Function Design
- Keep functions focused on a single responsibility
- Limit function parameters (prefer dataclasses for complex parameter sets)
- Use keyword-only arguments for optional parameters with defaults
- Return meaningful data structures

```python
# Good - Single responsibility
def validate_repository_url(url: str) -> bool:
    """Validate that URL appears to be a valid git repository."""
    # Implementation

def clone_repository(
    url: str,
    target_path: Path,
    *,  # Keyword-only arguments
    bare: bool = True,
    force: bool = False,
) -> CloneResult:
    """Clone repository with specific options."""
    # Implementation
```

### Resource Management
- Use context managers for resource cleanup
- Handle file operations safely
- Clean up temporary resources

```python
# Good
with CloneLockManager(repo_path) as lock:
    result = perform_clone(url, repo_path)
    return result

# Good
def read_config_file(path: Path) -> dict[str, Any]:
    """Read configuration from file."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
```

### Performance Considerations
- Use appropriate data structures for the task
- Avoid premature optimization
- Profile before optimizing
- Use generators for large datasets when appropriate

## Git Workflow

### Commit Messages
Follow conventional commit format with our specific requirements:

```
<type>(<scope>): <description>

<body>

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

#### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### Examples
```
feat(cli): add repository cloning command

Implement comprehensive repository cloning with progress tracking,
authentication support, and error handling.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Branch Naming
- Use descriptive branch names
- Include issue numbers when applicable
- Use hyphens to separate words

```
feature/repository-cloning
fix/config-validation-error
docs/api-documentation
```

## Tool Integration

### Ruff Configuration
Ruff handles most formatting automatically. Key rules we enforce:

- **Formatting**: Line length, quotes, indentation
- **Import sorting**: Automatic organization and sorting
- **Code quality**: Unused imports, variables, deprecated syntax
- **Security**: Basic security issue detection

### MyPy Integration
- Use strict mode for type checking
- Provide type hints for all public APIs
- Use `# type: ignore` sparingly with explanatory comments

### Pre-commit Hooks
Automated checks before each commit:

- Ruff formatting and linting
- MyPy type checking
- Test execution
- Commit message validation

## Common Patterns

### Configuration Management
```python
@dataclass
class RepositoryConfig:
    """Configuration for a single repository."""
    name: str
    source: dict[str, Any]
    auth_key: str | None = None
    storage: StorageConfig = field(default_factory=StorageConfig)

    @property
    def url(self) -> str:
        """Get repository URL."""
        return self.source["url"]
```

### Error Context
```python
def process_repository(config: RepositoryConfig) -> ProcessResult:
    """Process a repository configuration."""
    try:
        return _perform_processing(config)
    except Exception as e:
        logger.error(
            f"Failed to process repository {config.name}: {e}",
            extra={"repo_name": config.name, "repo_url": config.url}
        )
        raise ProcessingError(f"Repository processing failed: {config.name}") from e
```

### Progress Tracking
```python
def operation_with_progress(
    items: list[Any],
    callback: Callable[[ProgressInfo], None] | None = None,
) -> OperationResult:
    """Perform operation with optional progress tracking."""
    for i, item in enumerate(items):
        # Do work
        if callback:
            progress = ProgressInfo(
                completed=i + 1,
                total=len(items),
                current_item=str(item)
            )
            callback(progress)
```

## Anti-Patterns to Avoid

### Code Smells
- **Long parameter lists**: Use dataclasses or configuration objects
- **Deep nesting**: Extract methods or use early returns
- **Magic numbers**: Define named constants
- **Mutable default arguments**: Use `None` and create inside function

```python
# Avoid
def process_repos(repos, cache_size=1000, retry_count=3, timeout=30, ...):
    pass

# Good  
@dataclass
class ProcessingOptions:
    cache_size: int = 1000
    retry_count: int = 3
    timeout: int = 30

def process_repos(repos: list[str], options: ProcessingOptions | None = None):
    if options is None:
        options = ProcessingOptions()
```

### Import Anti-Patterns
```python
# Avoid
from module import *  # Pollutes namespace
import really.long.module.name as x  # Unclear abbreviation

# Good
import really.long.module.name as module_name
from module import specific_function, AnotherClass
```

## Enforcement

This style guide is enforced through:

1. **Automated tools**: Ruff, mypy, pre-commit hooks
2. **Code review**: Manual review of pull requests
3. **Documentation**: This guide and inline comments
4. **AI assistance**: AI tools follow the condensed style guide

For questions about style decisions not covered here, refer to:
1. Current codebase patterns
2. PEP 8
3. Google Python Style Guide
4. Team discussion and documentation updates

---

**Remember**: The goal is readable, maintainable code that serves the project's users and contributors. When in doubt, prioritize clarity over cleverness.
