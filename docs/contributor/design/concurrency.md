# Concurrency Architecture

> **Async/await patterns for concurrent git repository analysis**

## System Overview

Ca-Bhfuil's concurrency architecture enables efficient processing of multiple repositories simultaneously while maintaining responsive user interfaces. The design prioritizes async-first patterns with careful resource management for single-developer maintenance.

## Core Architectural Principles

### Async-First Design
- **I/O Operations**: All file, network, and database operations use async/await
- **Git Operations**: Thread pool wrappers for synchronous pygit2 calls
- **Progress Reporting**: Real-time updates through async queues
- **Resource Management**: Semaphores and connection pooling

### Concurrency Control Strategy
- **Repository Processing**: 3-5 concurrent repositories (configurable)
- **Network Operations**: Rate-limited HTTP clients with connection pooling
- **Database Access**: Connection pooling with transaction management
- **Git Operations**: Thread pool isolation for pygit2 synchronous operations

### Performance and Responsiveness
- **Non-blocking CLI**: Operations remain responsive during long tasks
- **Background Processing**: Data prefetching and analysis tasks
- **Progress Transparency**: Real-time progress bars and status updates
- **Efficient Resource Usage**: Connection reuse and intelligent caching

## System Components

### Service Layer Architecture

**AsyncRepositoryManager**
- Orchestrates concurrent repository operations
- Manages semaphore-controlled resource access
- Coordinates background task scheduling
- Provides progress reporting across operations

**AsyncTaskManager**
- Background task scheduling and lifecycle management
- Task result storage with automatic cleanup
- Status monitoring and health checks
- Data prefetching for improved responsiveness

**AsyncConfigManager**
- Configuration loading with file watching
- Cache management with TTL-based invalidation
- Concurrent file access with async locking
- Environment variable integration

### I/O Layer Architecture

**AsyncDatabaseManager**
- aiosqlite-based database operations with connection pooling
- Transaction management with automatic rollback
- Schema versioning and migration support
- Foreign key constraint enforcement

**AsyncHTTPClient**
- httpx.AsyncClient with connection and keepalive pooling
- Rate limiting to prevent API abuse
- Response caching with TTL-based invalidation
- Retry logic with exponential backoff
- Circuit breaker pattern for failing services

**File Operations**
- aiofiles for non-blocking file I/O
- Async configuration loading with change watching
- File locking for concurrent access protection
- Cache management with intelligent invalidation

### Git Operations Layer

**AsyncGitManager**
- Thread pool wrapper for synchronous pygit2 operations
- Async progress reporting with cross-thread communication
- Repository cloning with real-time progress updates
- Concurrent commit analysis and traversal
- Authentication handling for remote repositories

**Progress Tracking**
- AsyncProgressTracker for cross-thread progress updates
- Queue-based progress reporting to async consumers
- Structured progress data models
- Error handling and completion signaling

**Thread Pool Strategy**
- Dedicated thread pool for git operations
- 3-worker default to balance performance and resource usage
- Thread-safe communication between sync and async contexts
- Proper cleanup and resource management

### Network Operations Strategy

**HTTP Client Architecture**
- httpx.AsyncClient with configurable connection limits
- Rate limiting via semaphores to prevent API abuse
- Response caching with TTL-based invalidation
- Retry logic with exponential backoff
- Proper connection lifecycle management

**Issue Tracker Integration**
- Concurrent fetching of issue tracker data
- Provider-specific authentication handling
- Lazy loading with intelligent caching
- Error handling with graceful degradation

**Background Data Prefetching**
- Repository metadata prefetching
- Contributor information gathering
- Release data synchronization
- Concurrent data fetching with result aggregation

### CLI Integration Architecture

**Async-Sync Bridge Pattern**
- AsyncCLIBridge for Typer integration with async operations
- Event loop management across sync/async boundaries
- Progress display integration with Rich terminal output
- Exception handling and error propagation

**Progress Display Integration**
- Real-time progress bars during long operations
- Rich terminal formatting with spinners and progress bars
- Non-blocking progress updates via async queues
- User-friendly status messages and completion indicators

**Command Integration Strategy**
- Decorator pattern for adding async capabilities to CLI commands
- Consistent progress reporting across all async operations
- Error handling with user-friendly messages
- Backward compatibility with existing Typer command structure

## Background Task Architecture

### Task Management Strategy

**Task Lifecycle Management**
- Background analysis scheduling with unique task IDs
- Task status tracking (pending, running, completed, failed)
- Result storage with automatic cleanup
- Health monitoring and error reporting

**Background Operations**
- Repository data prefetching
- Issue tracker metadata synchronization
- Cache warming for frequently accessed data
- Long-running analysis tasks

**Resource Management**
- Automatic cleanup of completed task results
- Memory management for long-running tasks
- Cancellation support for abandoned operations
- Health checks and monitoring

## Error Handling and Resilience

### Resilience Patterns

**Retry Logic**
- Exponential backoff for transient failures
- Configurable retry attempts and delays
- Operation-specific retry strategies
- Comprehensive error logging and tracking

**Circuit Breaker Pattern**
- Service-level failure detection
- Automatic service isolation when failure threshold exceeded
- Recovery detection and circuit reset
- Graceful degradation for failing external services

**Timeout Management**
- Operation-specific timeout configuration
- Cancellation support for long-running operations
- Resource cleanup on timeout
- User feedback for timeout scenarios

### Operation Monitoring

**Performance Tracking**
- Operation timing and success rate monitoring
- Historical performance data collection
- Resource usage tracking
- Health checks for long-running operations

**Error Classification**
- Structured error reporting with context
- Error pattern detection and analysis
- User-friendly error messages
- Debug-level logging for troubleshooting

## Testing Strategy

### Async Testing Infrastructure

**pytest-asyncio Integration**
- Session-scoped event loop management
- Async fixture support with proper cleanup
- Mock async clients with simulated delays
- Integration test patterns for complete workflows

**Test Patterns**
- Concurrent operation testing with controlled parallelism
- Error scenario testing with partial failures
- Progress reporting verification
- Resource cleanup and memory leak detection

**Mock and Fixture Strategy**
- Async repository manager fixtures
- Mock HTTP clients with configurable responses
- Test data generation for various scenarios
- Isolation and cleanup for test reliability

## Implementation Guide

### Async Component Usage Patterns

#### Async Configuration Management

```python
from ca_bhfuil.core import async_config

# Initialize async config manager
config_manager = async_config.AsyncConfigManager()

# Load configuration asynchronously
global_config = await config_manager.load_configuration()

# Get specific repository configuration
repo_config = await config_manager.get_repository_config("repo-name")

# Validate configuration
errors = await config_manager.validate_configuration()
if errors:
    print(f"Configuration errors: {errors}")

# Generate default configuration files
await config_manager.generate_default_config()
```

#### Async Database Operations

```python
from ca_bhfuil.storage import async_database

# Initialize database manager
db_manager = async_database.AsyncDatabaseManager("path/to/database.db")
await db_manager.connect(pool_size=10)

# Execute queries
cursor = await db_manager.execute(
    "SELECT * FROM commits WHERE sha = ?",
    ["abc123"]
)

# Execute transactions
async def transaction_example():
    await db_manager.execute("BEGIN TRANSACTION")
    try:
        await db_manager.execute(
            "INSERT INTO commits (sha, message) VALUES (?, ?)",
            ["abc123", "Fix bug"]
        )
        await db_manager.execute("COMMIT")
    except Exception:
        await db_manager.execute("ROLLBACK")
        raise

await db_manager.close()
```

#### Async HTTP Client Usage

```python
from ca_bhfuil.integrations import async_http

# Initialize HTTP client
client = async_http.AsyncHTTPClient(
    base_url="https://api.github.com",
    headers={"Authorization": "token YOUR_TOKEN"}
)

# Make requests
try:
    response = await client.get("/repos/owner/repo")
    data = response.json()
except Exception as e:
    print(f"Request failed: {e}")

await client.close()
```

#### Async Git Operations

```python
from ca_bhfuil.core.git import async_git
from ca_bhfuil.core.models import progress

# Initialize git manager
git_manager = async_git.AsyncGitManager(max_workers=4)

# Run git operations in thread pool
def sync_git_operation():
    # Synchronous pygit2 operation
    return pygit2.Repository("/path/to/repo")

repo = await git_manager.run_in_executor(sync_git_operation)

# With progress reporting
def progress_callback(progress_obj: progress.CloneProgress):
    print(f"Cloning: {progress_obj.percent_complete}%")

# Cleanup
git_manager.shutdown()
```

#### Async Repository Management

```python
from ca_bhfuil.core import async_repository

# Initialize repository manager
repo_manager = async_repository.AsyncRepositoryManager(max_concurrent_tasks=3)

# Run concurrent operations
async def clone_repo(url: str):
    # Clone operation implementation
    pass

async def analyze_repo(path: str):
    # Analysis operation implementation
    pass

# Execute concurrent tasks
tasks = [
    clone_repo("https://github.com/user/repo1"),
    clone_repo("https://github.com/user/repo2"),
    analyze_repo("/path/to/repo3")
]

results = await repo_manager.run_concurrently(tasks)
```

#### Async Task Management

```python
from ca_bhfuil.core import async_tasks

# Initialize task manager
task_manager = async_tasks.AsyncTaskManager()

# Create background tasks
async def background_analysis():
    # Long-running analysis
    await asyncio.sleep(10)
    return {"commits_analyzed": 1000}

# Schedule background task
task_id = task_manager.create_task(background_analysis())

# Check task status
status = task_manager.get_status(task_id)
print(f"Task status: {status}")

# Get results when complete
result = task_manager.get_result(task_id)
```

#### Async Progress Tracking

```python
from ca_bhfuil.core import async_progress
from ca_bhfuil.core.models import progress

# Define progress callback
async def progress_callback(progress_obj: progress.OperationProgress):
    print(f"Progress: {progress_obj.completed}/{progress_obj.total}")

# Initialize progress tracker
tracker = async_progress.AsyncProgressTracker(progress_callback)

# Report progress from synchronous context
def sync_operation():
    # Some synchronous operation
    tracker.report_progress(
        progress.OperationProgress(
            total=100,
            completed=50,
            status="Processing..."
        )
    )

# Cleanup
await tracker.shutdown()
```

#### Async Error Handling

```python
from ca_bhfuil.core import async_errors

# Initialize error handler
error_handler = async_errors.AsyncErrorHandler(
    attempts=3,
    initial_backoff=1.0,
    max_backoff=10.0
)

# Retry operations with exponential backoff
async def unreliable_operation():
    # Operation that might fail
    pass

result = await error_handler.retry(
    unreliable_operation(),
    retry_on=(ConnectionError, TimeoutError)
)
```

#### Async Operation Monitoring

```python
from ca_bhfuil.core import async_monitor

# Initialize monitor
monitor = async_monitor.AsyncOperationMonitor()

# Monitor async operations
@monitor.timed
async def monitored_operation():
    await asyncio.sleep(1)
    return "result"

# Get operation statistics
stats = monitor.stats
print(f"Operation calls: {stats['monitored_operation']['calls']}")
```

### CLI Integration Patterns

#### Async Command Implementation

```python
from ca_bhfuil.cli.async_bridge import async_command, with_progress
import typer

@typer.command()
@async_command
async def clone_repositories(
    urls: list[str] = typer.Argument(..., help="Repository URLs to clone")
):
    """Clone multiple repositories concurrently."""

    async def clone_all():
        # Implementation here
        pass

    await with_progress(
        clone_all(),
        "Cloning repositories...",
        show_progress=True
    )
```

#### Progress Display Integration

```python
from ca_bhfuil.cli.async_bridge import with_progress

async def long_operation():
    # Long-running operation
    pass

# Run with progress display
result = await with_progress(
    long_operation(),
    "Processing...",
    show_progress=True
)
```

### Best Practices

#### Resource Management

```python
# Always use async context managers
async with AsyncHTTPClient() as client:
    response = await client.get("https://api.example.com")

# Proper cleanup
git_manager = AsyncGitManager()
try:
    # Use git manager
    pass
finally:
    git_manager.shutdown()
```

#### Error Handling

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

#### Progress Reporting

```python
# Use structured progress models
async def operation_with_progress(progress_callback=None):
    total_steps = 100
    for i in range(total_steps):
        # Do work
        if progress_callback:
            await progress_callback(
                progress.OperationProgress(
                    total=total_steps,
                    completed=i + 1,
                    status=f"Processing step {i + 1}"
                )
            )
```

#### Concurrent Operations

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

### Testing Async Code

#### Async Test Fixtures

```python
import pytest
from ca_bhfuil.core import async_config

@pytest.fixture
async def async_config_manager():
    """Provide async config manager for tests."""
    manager = async_config.AsyncConfigManager()
    yield manager
    # Cleanup if needed

@pytest.mark.asyncio
async def test_async_config_loading(async_config_manager):
    """Test async configuration loading."""
    config = await async_config_manager.load_configuration()
    assert config is not None
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

## Design Benefits

This concurrency architecture enables:

### Performance Improvements
- **Concurrent Repository Processing**: 3-5 repositories processed simultaneously
- **Non-blocking I/O**: All file, network, and database operations asynchronous
- **Resource Efficiency**: Connection pooling and intelligent caching
- **Background Operations**: Data prefetching improves perceived performance

### User Experience Enhancements
- **Responsive CLI**: Interface remains interactive during long operations
- **Real-time Progress**: Detailed progress reporting for all async operations
- **Graceful Error Handling**: User-friendly messages with retry capabilities
- **Cancellation Support**: Operations can be interrupted cleanly

### Developer Benefits
- **Single-Developer Friendly**: Clear async patterns without excessive complexity
- **Type Safety**: Full type hints for all async operations
- **Testing Support**: Comprehensive async testing infrastructure
- **Monitoring**: Operation performance and health tracking

## Integration with Ca-Bhfuil Architecture

This concurrency design integrates with the broader system architecture:
- **Local-First**: All async operations work offline with local storage
- **Performance-Focused**: Designed for repositories with 10k+ commits
- **Privacy-Preserving**: Async operations maintain local-only data handling
- **Modular Design**: Async components integrate cleanly with existing architecture

## Cross-References

- **Implementation details**: See `ai/memory/async-conversion-tasks.md`
- **System architecture**: See [architecture-overview.md](architecture-overview.md)
- **Technology choices**: See [technology-decisions.md](technology-decisions.md)
- **Repository management**: See [repository-management.md](repository-management.md)
- **Development workflow**: See [development-workflow.md](development-workflow.md)

---

This architecture provides Ca-Bhfuil with concurrent processing capabilities while maintaining the tool's core principles of local-first operation, performance focus, and single-developer maintainability.

---

**Implementation Status (2025-01-27):** The foundational async infrastructure has been fully implemented and is ready for use. All core async components are functional and tested. The next step is to integrate these components into the application's feature logic as part of core functionality development.
