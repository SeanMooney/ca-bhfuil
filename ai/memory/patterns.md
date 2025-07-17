# Development Patterns Library

> **Reusable solutions and patterns for ca-bhfuil development**
>
> **Last Updated**: 2025-07-17

## Code Patterns That Work Well

### Import Patterns
- **Always import modules, never functions/classes directly**
- Use `from package import module` over `import package.module` for submodules
- Example: `from rich import console` not `import rich.console`
- Example: `pathlib.Path()` not `from pathlib import Path`

### Error Handling Patterns
- Use custom exception hierarchy with base `CaBhfuilError`
- Always chain exceptions with `raise NewError() from original_error`
- Log errors with context: `logger.error(f"Operation failed for {item}: {error}")`

### Testing Patterns
- Use descriptive test names: `test_clone_with_invalid_url_raises_error`
- Group related tests in classes: `class TestRepositoryCloner`
- Use fixtures for common setup: `@pytest.fixture def temp_repo_path`
- Mock external dependencies with `autospec=True`

### Configuration Patterns
- Use Pydantic models for all configuration structures
- Validate configuration at load time, not usage time
- Use environment variables for deployment-specific overrides
- Keep sensitive data in separate files with restricted permissions

## Testing Strategies That Have Been Effective

### Unit Testing
- Test one thing at a time
- Use mock objects for external dependencies
- Verify both positive and negative cases
- Include edge cases and error conditions

### Integration Testing
- **Environment Isolation**: Always use XDG environment variables for complete isolation
- **Real Systems**: Use actual git repositories, SQLite databases, and filesystem operations
- **TestRepository Fixture**: Create real git repositories with commits and branches
- **File Protocol**: Use `file://` URLs for local repository testing
- **No Heavy Mocking**: Mock only external network calls, use real systems otherwise

**Environment Isolation Pattern**:
```python
# CORRECT: Use proper XDG fixtures
@pytest.fixture
def fake_home_dir():
    """Create fake home directory with proper XDG structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_home = pathlib.Path(tmp_dir)
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

def test_integration_workflow(isolated_xdg_environment):
    """Integration test with proper XDG isolation."""
    with isolated_xdg_environment() as xdg_dirs:
        # All operations use isolated XDG directories
        config_manager = AsyncConfigManager(xdg_dirs["config"] / "ca-bhfuil")
        # Test operations...
```

**Real Repository Pattern**:
```python
def test_with_real_git_repo():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create real git repository
        source_repo = repositories.TestRepository(tmp_dir / "source")
        source_repo.add_file("README.md", "# Test")
        source_repo.commit("Initial commit")

        # Clone using file:// protocol
        repo_config = config.RepositoryConfig(
            name="test-repo",
            source={"url": f"file://{source_repo.path}", "type": "git"},
        )

        # Test with real git operations
        result = sync_repository(repo_config)
        assert result.success is True
```

**Database Testing Pattern**:
```python
async def test_with_real_database():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = tmp_dir / "test.db"
        db_manager = SQLModelDatabaseManager(db_path)
        await db_manager.initialize()

        # Test with real database operations
        await db_manager.register_repository(repo_config)
```

### Test Organization
- Mirror source structure in tests/ directory
- Use descriptive test class and method names
- Group related tests in classes
- Use fixtures for common test setup

## Anti-Patterns to Avoid

### Import Anti-Patterns
- **Never use `from module import *`** - pollutes namespace
- **Never import functions/classes directly** - makes code less clear
- **Don't mix import styles** - be consistent within a module
- **Avoid circular imports** - indicates design problems

### Code Structure Anti-Patterns
- **Long parameter lists** - use dataclasses or configuration objects
- **Deep nesting** - extract methods or use early returns
- **Magic numbers** - define named constants
- **Mutable default arguments** - use None and create inside function

### Testing Anti-Patterns
- **Testing implementation details** - test behavior, not internals
- **Overly complex test setup** - indicates code design issues
- **Not testing error conditions** - leads to poor error handling
- **Shared test state** - tests should be independent
- **Wrong test type**:
  - **Unit tests with real systems** - breaks isolation and speed
  - **Integration tests with heavy mocking** - defeats purpose of end-to-end testing
  - **Mixed approaches** - unclear test intent and maintenance issues
- **Poor environment isolation**:
  - **Using system directories** - creates pollution and conflicts
  - **Not using XDG variables** - tests affect each other
  - **Not cleaning up resources** - resource leaks and failures
  - **Incorrect XDG structure** - pointing XDG variables to wrong directories
  - **Manual XDG setup** - not using reusable fixtures
- **Fake git repositories**:
  - **Creating fake .git directories** - doesn't test real git operations
  - **Mocking git operations in integration tests** - misses real behavior
  - **Using hardcoded paths** - breaks path resolution logic
- **Wrong XDG patterns**:
  - **`XDG_CONFIG_HOME=str(tmp_dir / "config")`** - should be base directory
  - **Mixed source/app directories** - source repos and app data in same temp dir
  - **No fixture separation** - not separating git repos from XDG directories

### Configuration Anti-Patterns
- **Hardcoded values** - use configuration files or constants
- **No validation** - validate configuration early and clearly
- **Mixing concerns** - separate user config from system config
- **No defaults** - provide sensible defaults for optional settings

## Architecture Patterns

### Layered Architecture
- **CLI Layer**: User interface and command parsing
- **Core Layer**: Business logic and domain models
- **Storage Layer**: Data persistence and caching
- **Integration Layer**: External service interactions

### Dependency Injection
- Pass dependencies explicitly rather than importing them
- Use configuration objects to manage dependencies
- Make external dependencies injectable for testing
- Keep core logic independent of external systems

### Error Boundaries
- Handle errors at appropriate abstraction levels
- Use specific exception types for different error conditions
- Provide clear error messages with actionable information
- Log errors with sufficient context for debugging

### Data Flow Patterns
- Use Pydantic models for data validation and serialization
- Keep data transformations explicit and testable
- Use typed interfaces between components
- Validate data at system boundaries

## Performance Patterns

### Caching Strategies
- Cache expensive operations (git operations, API calls)
- Use appropriate cache invalidation strategies
- Monitor cache hit rates in development
- Consider memory usage of cached data

### Resource Management
- Use context managers for file operations
- Clean up temporary resources promptly
- Handle concurrent operations safely
- Use appropriate data structures for the task

## Documentation Patterns

### Code Documentation
- Write docstrings for all public interfaces
- Include examples in docstrings for complex functions
- Document non-obvious design decisions
- Keep comments focused on "why" not "what"

### Memory System Usage
- Update memory files after learning new patterns
- Document architectural decisions with rationale
- Create session logs for complex development work
- Maintain pattern library with successful approaches

## Integration Patterns

### Git Operations
- Always use pygit2 for performance
- Handle git errors gracefully with specific exception types
- Use bare repositories for better performance
- Implement proper locking for concurrent operations

### CLI Design
- Follow consistent command patterns: `ca-bhfuil <resource> <operation>`
- Use Rich for beautiful terminal output
- Provide both verbose and quiet modes
- Include helpful error messages with suggestions

### Configuration Management
- Use XDG Base Directory specification
- Separate user config from authentication
- Provide clear validation error messages
- Support both YAML and environment variable configuration

## Database Schema Evolution Patterns

### Model-Documentation Synchronization
**Critical Requirement**: When `src/ca_bhfuil/storage/database/models.py` changes, documentation must be updated automatically.

**Workflow Pattern**:
1. **Model Changes**: Any modification to SQLModel classes
2. **Design Doc Update**: Automatically update `docs/contributor/design/data-storage-design.md`
3. **Migration Generation**: Create new Alembic migration if schema changes
4. **AI Memory Update**: Document the changes in architecture decisions

**Implementation Requirements**:
- AI assistants MUST check for model changes at start of session
- AI assistants MUST update design documentation when models change
- AI assistants MUST generate migrations for schema changes
- All changes MUST follow the AI style guide import patterns

**Key Files to Monitor**:
- `src/ca_bhfuil/storage/database/models.py` - Source of truth for data models
- `docs/contributor/design/data-storage-design.md` - Architecture documentation
- `alembic/versions/` - Database migrations
- `ai/memory/architecture-decisions.md` - Decision history

**Automation Triggers**:
- When starting a development session, check git diff for model changes
- When making model changes, immediately update documentation
- When schema changes, generate migration with descriptive name
- Document rationale for model changes in architecture decisions

### Alembic Migration Patterns
**Style Guide Compliance**:
- Use `from collections import abc` not `from typing import Sequence`
- Use modern union syntax: `str | None` not `Optional[str]`
- Follow module-only import pattern: `import sqlalchemy as sa`
- Include descriptive migration names and docstrings

**Migration Naming Convention**:
- Format: `YYYY_MM_DD_descriptive_change_name`
- Examples: `2025_06_30_add_commit_branch_relationship`
- Include rationale in migration docstring

---

**Remember**: Patterns should be living documents. Update this file when you discover new effective patterns or identify anti-patterns to avoid.
