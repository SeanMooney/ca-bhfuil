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

## Testing Strategy

### Testing Philosophy

Ca-Bhfuil uses a **dual-track testing approach** with clear separation between unit and integration tests:

#### Unit Tests (`tests/unit/`)
- **Purpose**: Fast, isolated testing of individual components
- **Mocking**: Heavy mocking of external dependencies is **required**
- **Scope**: Single class/function, isolated from filesystem, network, database
- **Speed**: Must be fast (<100ms per test)
- **Dependencies**: Mock all external systems (git, database, filesystem, network)

#### Integration Tests (`tests/integration/`)
- **Purpose**: End-to-end testing of real system interactions
- **Mocking**: Minimal mocking - use real systems **preferred**
- **Scope**: Multiple components working together
- **Speed**: Can be slower (1-10s per test)
- **Dependencies**: Use real git repositories, temporary databases, actual file operations

### Test Strategy Matrix

| Test Type | Git Operations | Database | Filesystem | Network | Mocking Level |
|-----------|---------------|----------|------------|---------|---------------|
| Unit      | Mock git calls | Mock DB  | Mock paths | Mock HTTP | Heavy (90%+) |
| Integration| Real git repos | Temp DB | Temp dirs | Real/Skip | Light (10%) |

### Unit Test Guidelines

**What to Mock in Unit Tests**:
- All git operations (pygit2 calls)
- Database operations (SQLAlchemy, async sessions)
- Filesystem operations (pathlib.Path methods)
- Network requests (HTTP calls)
- External processes (subprocess calls)

**Unit Test Structure**:
```python
class TestGitOperations:
    """Unit tests for git operations."""

    @pytest.fixture
    def mock_repo(self):
        """Mock git repository."""
        return mock.Mock(spec=pygit2.Repository)

    @mock.patch("pygit2.Repository")
    def test_clone_repository_success(self, mock_repo_class, mock_repo):
        """Test successful repository cloning."""
        mock_repo_class.return_value = mock_repo
        mock_repo.is_empty = False

        result = git_operations.clone_repository("fake-url", "/fake/path")

        assert result.success is True
        mock_repo_class.assert_called_once_with("/fake/path")

    @mock.patch("pathlib.Path.exists", return_value=False)
    def test_clone_repository_path_missing(self, mock_exists):
        """Test cloning when target path doesn't exist."""
        result = git_operations.clone_repository("fake-url", "/missing/path")

        assert result.success is False
        assert "path doesn't exist" in result.error
```

### Integration Test Guidelines

**What NOT to Mock in Integration Tests**:
- Git operations (use real git repositories)
- Database operations (use temporary SQLite databases)
- Filesystem operations (use temporary directories)
- Configuration loading (use real config files in temp dirs)

**Integration Test Structure**:
```python
class TestRepositorySync:
    """Integration tests for repository synchronization."""

    @pytest.mark.asyncio
    async def test_full_sync_workflow(self, integration_test_environment):
        """Test complete sync workflow with real systems."""
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

**Critical**: Integration tests must use proper XDG fixtures to ensure complete isolation:

#### Correct XDG Fixture Pattern

Create reusable fixtures in `tests/integration/conftest.py`:

```python
@pytest.fixture
def fake_home_dir():
    """Create a fake home directory with proper XDG structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_home = pathlib.Path(tmp_dir)

        # Create standard XDG directory structure
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
```

#### Usage in Integration Tests

```python
@pytest.mark.asyncio
async def test_with_proper_xdg_isolation(isolated_xdg_environment):
    """Integration test with proper XDG isolation."""
    with isolated_xdg_environment() as xdg_dirs:
        # Initialize components with XDG directories
        config_manager = AsyncConfigManager(xdg_dirs["config"] / "ca-bhfuil")
        db_manager = SQLModelDatabaseManager(xdg_dirs["state"] / "test.db")

        # All config/cache/state operations happen in isolated XDG structure
        await config_manager.generate_default_config()
        await db_manager.initialize()
```

#### What This Creates

The fixture creates a proper XDG directory structure:
```
fake_home/
├── .config/          (XDG_CONFIG_HOME points here)
├── .cache/           (XDG_CACHE_HOME points here)
└── .local/
    └── state/        (XDG_STATE_HOME points here)
```

#### Common Anti-Pattern (AVOID)

```python
# WRONG: Incorrect XDG structure
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
    """This creates wrong directory structure."""
    pass
```

### Test Repository Creation

Use the `TestRepository` fixture for creating real git repositories:

```python
from tests.fixtures import repositories

def test_with_real_repo():
    """Test with actual git repository."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = pathlib.Path(tmp_dir) / "test-repo"
        test_repo = repositories.TestRepository(repo_path)

        # Add commits
        test_repo.add_file("file1.txt", "content")
        test_repo.commit("Add file1", "commit1")

        # Create branches
        test_repo.create_branch("feature")
        test_repo.checkout_branch("feature")

        # Test with real git operations
        result = analyze_repository(repo_path)
        assert result.commit_count == 1
        assert "feature" in result.branches
```

### Database Testing

**Unit Tests**: Mock database operations
```python
@mock.patch("sqlalchemy.create_engine")
def test_database_connection(self, mock_create_engine):
    """Test database connection logic."""
    mock_create_engine.return_value = mock_engine
    # Test connection logic
```

**Integration Tests**: Use real temporary databases
```python
async def test_repository_registration():
    """Test repository registration with real database."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = pathlib.Path(tmp_dir) / "test.db"
        db_manager = SQLModelDatabaseManager(db_path)
        await db_manager.initialize()

        # Test with real database operations
        repo_id = await db_manager.register_repository(repo_config)
        assert repo_id > 0
```

### Test Naming Conventions

**Unit Tests**:
- `test_method_name_condition_expected_outcome`
- `test_clone_repository_success`
- `test_clone_repository_invalid_url_raises_error`

**Integration Tests**:
- `test_workflow_name_end_to_end`
- `test_repo_add_sync_workflow`
- `test_full_clone_and_analyze_workflow`

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_functionality():
    """Unit test marker."""
    pass

@pytest.mark.integration
def test_integration_workflow():
    """Integration test marker."""
    pass

@pytest.mark.slow
def test_long_running_operation():
    """Mark slow tests."""
    pass

@pytest.mark.network
def test_network_dependent():
    """Mark tests requiring network."""
    pass
```

### Test Performance Guidelines

**Unit Tests**:
- Must complete in <100ms each
- Use mocking to avoid I/O operations
- Run in parallel without conflicts

**Integration Tests**:
- Should complete in <10s each
- Use temporary resources that clean up automatically
- May run sequentially if needed for resource sharing

### Test Quality Checklist

Before committing tests, verify:

- [ ] **Unit tests mock all external dependencies**
- [ ] **Integration tests use real systems with proper isolation**
- [ ] **XDG environment variables are used for integration tests**
- [ ] **Temporary resources are properly cleaned up**
- [ ] **Test names clearly describe what is being tested**
- [ ] **Tests are deterministic and don't depend on external state**
- [ ] **Error cases are tested alongside success cases**

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
