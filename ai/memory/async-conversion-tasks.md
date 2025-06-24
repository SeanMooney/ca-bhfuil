# Async Conversion Tasks

## Overview

This document outlines the specific tasks to convert Ca-Bhfuil from synchronous to async/await patterns based on the comprehensive architecture defined in `docs/contributor/design/concurrency.md`. This conversion plan works alongside `bootstrap-tasks.md` to modernize the codebase.

**Target Architecture**: Async-first design with concurrent repository processing, non-blocking I/O, and responsive CLI operations.

## Current State Analysis

### Existing Synchronous Components
- ✅ **Configuration System**: XDG-compliant config management (sync file operations)
- ✅ **CLI Framework**: Typer-based commands (sync-only interface)
- ✅ **Storage Layer**: SQLite schema and diskcache wrapper (sync operations)
- ✅ **Git Operations**: Basic pygit2 integration (sync git operations)
- ❌ **Missing**: Any async/await patterns throughout codebase

### Required Dependencies (Already in pyproject.toml)
- ✅ **aiofiles**: Async file operations
- ✅ **pytest-asyncio**: Async testing support
- ⏳ **aiosqlite**: Async SQLite operations (needs to be added)
- ⏳ **watchfiles**: Async file watching (needs to be added)

## Phase 1: Foundation Dependencies and Models (Priority 1)

### Task 1.1: Update Dependencies for Async
**Estimated Effort**: 20 minutes  
**Dependencies**: None

Add missing async dependencies to pyproject.toml:
```toml
aiosqlite = ">=0.19.0"
watchfiles = ">=0.21.0"
```

Update pytest configuration for async mode:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Success Criteria**:
- [ ] aiosqlite and watchfiles installed
- [ ] pytest-asyncio configured for auto mode
- [ ] Dependencies resolve without conflicts

### Task 1.2: Create Async Progress Models
**Estimated Effort**: 45 minutes  
**Dependencies**: Task 1.1

Implement progress tracking models in `src/ca_bhfuil/core/models/progress.py`:
- `OperationProgress` - Generic operation progress reporting
- `CloneProgress` - Git clone progress with stats
- `AnalysisProgress` - Repository analysis progress
- `TaskStatus` enum - Background task status tracking

**Success Criteria**:
- [ ] Progress models with proper Pydantic validation
- [ ] Type-safe progress callbacks
- [ ] JSON serialization support
- [ ] Integration with existing models

### Task 1.3: Create Async Result Models
**Estimated Effort**: 30 minutes  
**Dependencies**: Task 1.2

Implement operation result models in `src/ca_bhfuil/core/models/results.py`:
- `CloneResult` - Repository clone operation results
- `AnalysisResult` - Repository analysis results  
- `SearchResult` - Search operation results
- Error handling patterns for async operations

**Success Criteria**:
- [ ] Result models handle success and failure cases
- [ ] Exception information captured properly
- [ ] Duration and metadata tracking
- [ ] Compatible with asyncio.gather exception handling

## Phase 2: Async I/O Layer (Priority 2)

### Task 2.1: Async Configuration Manager
**Estimated Effort**: 1.5 hours  
**Dependencies**: Task 1.1, existing config.py

Create `src/ca_bhfuil/core/async_config.py` implementing `AsyncConfigManager`:
- Async file operations using aiofiles
- Configuration caching with TTL
- File locking for concurrent access
- Configuration change watching with watchfiles

**Success Criteria**:
- [ ] `load_configuration()` operates asynchronously
- [ ] File operations non-blocking with aiofiles
- [ ] Cache management with time-based invalidation
- [ ] File change watching triggers callbacks
- [ ] Thread-safe operations with asyncio.Lock

### Task 2.2: Async Database Manager
**Estimated Effort**: 2 hours  
**Dependencies**: Task 1.1, existing storage layer

Create `src/ca_bhfuil/storage/async_database.py` implementing `AsyncDatabaseManager`:
- aiosqlite-based database operations
- Connection pooling with semaphores
- Transaction support with rollback
- Schema versioning and setup

**Success Criteria**:
- [ ] `execute_query()` and `execute_transaction()` async
- [ ] Connection pooling limits concurrent access
- [ ] Proper transaction handling with exceptions
- [ ] Database schema setup non-blocking
- [ ] Foreign key constraints enabled

### Task 2.3: Async HTTP Client
**Estimated Effort**: 1.5 hours  
**Dependencies**: Task 1.1

Create `src/ca_bhfuil/integrations/async_http.py` implementing `AsyncHTTPClient`:
- httpx.AsyncClient with connection pooling
- Rate limiting with semaphores
- Response caching with TTL
- Retry logic with exponential backoff

**Success Criteria**:
- [ ] HTTP operations use httpx.AsyncClient
- [ ] Connection pooling and keepalive configured
- [ ] Rate limiting prevents API abuse
- [ ] Cache reduces redundant requests
- [ ] Retry logic handles transient failures

## Phase 3: Async Git Operations (Priority 3)

### Task 3.1: Async Git Manager
**Estimated Effort**: 2.5 hours  
**Dependencies**: Task 1.2, existing git operations

Create `src/ca_bhfuil/core/git/async_git.py` implementing `AsyncGitManager`:
- ThreadPoolExecutor wrapper for pygit2 operations
- Async progress reporting for git operations
- Thread-safe progress updates
- Repository information caching

**Success Criteria**:
- [ ] pygit2 operations wrapped in thread pool
- [ ] `clone_repository()` reports progress asynchronously
- [ ] Thread-safe communication between sync/async contexts
- [ ] Repository info operations non-blocking
- [ ] Commit analysis operations asynchronous

### Task 3.2: Progress Tracking Infrastructure
**Estimated Effort**: 1 hour  
**Dependencies**: Task 1.2, Task 3.1

Create `src/ca_bhfuil/core/async_progress.py` implementing `AsyncProgressTracker`:
- Queue-based progress reporting
- Cross-thread progress updates
- Progress aggregation and reporting
- Callback management

**Success Criteria**:
- [ ] Progress updates flow from threads to async context
- [ ] Multiple operations can report progress simultaneously
- [ ] Progress callbacks receive structured updates
- [ ] Memory-efficient progress queue management

## Phase 4: Async Service Layer (Priority 4)

### Task 4.1: Async Repository Manager
**Estimated Effort**: 3 hours  
**Dependencies**: Task 3.1, Task 2.1

Create `src/ca_bhfuil/core/async_repository.py` implementing `AsyncRepositoryManager`:
- Concurrent repository operations with semaphores
- Background task management
- Repository analysis coordination
- Cross-repository search operations

**Success Criteria**:
- [ ] `clone_repositories()` processes multiple repos concurrently
- [ ] `analyze_repositories()` with configurable concurrency
- [ ] `search_across_repositories()` aggregates results
- [ ] Semaphore-controlled resource management
- [ ] Exception handling preserves partial results

### Task 4.2: Async Task Manager
**Estimated Effort**: 2 hours  
**Dependencies**: Task 4.1

Create `src/ca_bhfuil/core/async_tasks.py` implementing `AsyncTaskManager`:
- Background task scheduling and tracking
- Task result storage and cleanup
- Task status monitoring
- Repository data prefetching

**Success Criteria**:
- [ ] Background analysis tasks run independently
- [ ] Task status tracking (pending, running, completed, failed)
- [ ] Result retrieval with error handling
- [ ] Automatic cleanup of old task results
- [ ] Data prefetching improves responsiveness

## Phase 5: CLI Integration Bridge (Priority 5)

### Task 5.1: Async-Sync CLI Bridge
**Estimated Effort**: 2 hours  
**Dependencies**: Task 4.1

Create `src/ca_bhfuil/cli/async_bridge.py` implementing `AsyncCLIBridge`:
- Sync-to-async operation bridging for Typer
- Rich progress display integration
- Event loop management
- Exception handling across sync/async boundary

**Success Criteria**:
- [ ] `run_async()` properly manages event loops
- [ ] Progress display updates during long operations
- [ ] Exceptions propagate correctly to CLI
- [ ] Compatible with existing Typer command structure

### Task 5.2: Update CLI Commands for Async
**Estimated Effort**: 1.5 hours  
**Dependencies**: Task 5.1, existing CLI

Update `src/ca_bhfuil/cli/main.py` to use async operations:
- Integrate AsyncCLIBridge with existing commands
- Add progress display to repository operations
- Update command implementations for async patterns
- Maintain backward compatibility

**Success Criteria**:
- [ ] Existing CLI commands work with async backend
- [ ] Progress bars appear for long-running operations
- [ ] Responsive CLI during concurrent operations
- [ ] Error messages remain user-friendly
- [ ] Command help and completion unchanged

## Phase 6: Error Handling and Resilience (Priority 6)

### Task 6.1: Async Error Handler
**Estimated Effort**: 1.5 hours  
**Dependencies**: All previous phases

Create `src/ca_bhfuil/core/async_errors.py` implementing `AsyncErrorHandler`:
- Retry logic with exponential backoff
- Timeout handling for async operations
- Circuit breaker pattern implementation
- Centralized error logging and monitoring

**Success Criteria**:
- [ ] `handle_with_retry()` implements exponential backoff
- [ ] `handle_with_timeout()` prevents hanging operations
- [ ] Circuit breaker prevents cascade failures
- [ ] Error metrics and logging integration

### Task 6.2: Operation Monitoring
**Estimated Effort**: 1 hour  
**Dependencies**: Task 6.1

Create `src/ca_bhfuil/core/async_monitor.py` implementing `AsyncOperationMonitor`:
- Operation timing and success tracking
- Performance statistics collection
- Health monitoring for long-running operations
- Resource usage tracking

**Success Criteria**:
- [ ] Operation statistics collected automatically
- [ ] Performance metrics available for analysis
- [ ] Health checks for background operations
- [ ] Memory and resource leak detection

## Phase 7: Testing Infrastructure (Priority 7)

### Task 7.1: Async Test Fixtures
**Estimated Effort**: 2 hours  
**Dependencies**: All async components

Create comprehensive async test fixtures in `tests/conftest.py`:
- Async repository manager fixtures
- Mock HTTP client for testing
- Async database fixtures
- Event loop management for tests

**Success Criteria**:
- [ ] Async fixtures work with pytest-asyncio
- [ ] Mock objects support async operations
- [ ] Test isolation with separate event loops
- [ ] Fixtures handle setup and teardown properly

### Task 7.2: Async Integration Tests
**Estimated Effort**: 2.5 hours  
**Dependencies**: Task 7.1

Create `tests/test_async_integration.py` with comprehensive async tests:
- Concurrent repository operations
- Error handling in async context
- Progress reporting verification
- Background task testing

**Success Criteria**:
- [ ] Concurrent operations tested thoroughly
- [ ] Error scenarios handled correctly
- [ ] Progress callbacks receive expected updates
- [ ] Background tasks complete successfully
- [ ] Performance characteristics verified

## Phase 8: Migration and Compatibility (Priority 8)

### Task 8.1: Gradual Migration Strategy
**Estimated Effort**: 1 hour  
**Dependencies**: All async implementations

Create migration utilities in `src/ca_bhfuil/core/migration.py`:
- Compatibility layer for existing synchronous code
- Gradual migration helpers
- Feature flags for async vs sync operations
- Configuration for async behavior

**Success Criteria**:
- [ ] Existing synchronous code continues working
- [ ] Async operations can be enabled incrementally
- [ ] Feature flags control migration pace
- [ ] Configuration supports both modes

### Task 8.2: Documentation and Examples
**Estimated Effort**: 1 hour  
**Dependencies**: Task 8.1

Update documentation for async usage:
- Update `docs/design/concurrency.md` with implementation notes
- Add async usage examples to CLI help
- Update development documentation
- Create migration guide for users

**Success Criteria**:
- [ ] Documentation reflects actual implementation
- [ ] Examples demonstrate async capabilities
- [ ] Migration path clearly documented
- [ ] Performance benefits explained

## Success Criteria for Complete Async Conversion

The async conversion is complete when:

- [ ] **Concurrent Operations**: Multiple repositories can be processed simultaneously
- [ ] **Non-blocking CLI**: CLI remains responsive during long operations
- [ ] **Progress Reporting**: Real-time progress for all async operations
- [ ] **Resource Management**: Connection pooling and semaphore control working
- [ ] **Error Resilience**: Retry logic, timeouts, and circuit breakers functional
- [ ] **Background Tasks**: Repository analysis can run in background
- [ ] **Compatibility**: Existing CLI commands continue working
- [ ] **Testing**: Comprehensive async test coverage
- [ ] **Performance**: Demonstrable improvement in concurrent scenarios

## Implementation Notes

### Critical Patterns to Follow

1. **Module-Only Imports**: Follow ai/memory/ai-style-guide.md patterns
   ```python
   import asyncio
   import pathlib
   from collections import abc
   from ca_bhfuil.core import async_config
   ```

2. **Error Handling**: Always use specific exceptions
   ```python
   try:
       result = await operation()
   except asyncio.TimeoutError:
       raise OperationTimeoutError(f"Operation timed out")
   except Exception as e:
       logger.error(f"Operation failed: {e}")
       raise
   ```

3. **Resource Management**: Use async context managers
   ```python
   async with AsyncHTTPClient() as client:
       results = await client.fetch_data(urls)
   ```

4. **Progress Reporting**: Implement structured progress updates
   ```python
   async def operation(*, progress_callback=None):
       if progress_callback:
           await progress_callback(OperationProgress(completed=50, total=100))
   ```

### Integration with Existing Code

- **Configuration**: Async config manager supplements existing sync manager
- **Storage**: Async database manager works alongside existing schema
- **CLI**: Bridge pattern preserves existing Typer command structure
- **Git Operations**: Thread pool wrapper maintains pygit2 compatibility

### Performance Targets

- **Concurrent Repository Processing**: 3-5 repositories simultaneously
- **CLI Responsiveness**: Sub-100ms response to user input during operations
- **Progress Updates**: 10Hz (100ms intervals) for smooth progress bars
- **Resource Limits**: Connection pooling prevents resource exhaustion

### Maintenance Considerations

- **Single Developer Friendly**: Clear async patterns, minimal complexity
- **Type Safety**: Full type hints for all async operations
- **Error Messages**: User-friendly async error reporting
- **Documentation**: Inline documentation for async patterns

## Dependencies and Prerequisites

### ✅ Bootstrap Foundation Ready
- **Configuration System**: XDG-compliant config with Pydantic models
- **CLI Framework**: Typer commands with Rich output established
- **Storage Schema**: SQLite schema defined and tested
- **Testing Framework**: pytest with fixtures and patterns established

### 🔄 Parallel Development Possible
- **Git Operations**: Basic pygit2 integration → Async wrappers can be developed
- **Repository Management**: Core functionality → Async version supplements

### 🚀 Ready to Begin
Async conversion can start immediately with dependency setup and model creation, then proceed through I/O layer while basic git operations are finalized.

**Recommendation**: Start with Phase 1 (dependencies and models) to establish async foundation in parallel with completing synchronous git operations.

## Current Development Notes

### Session Status
**Last Updated**: 2025-06-27  
**Status**: Task list refactored and ready for implementation  
**Next Session Priority**: Phase 1 - Dependencies and foundation models

### Implementation Readiness
- All tasks clearly defined with effort estimates
- Dependencies mapped and prerequisites identified
- Success criteria established for each phase
- Integration strategy with existing codebase defined

### Key Insights from Refactoring
- Async conversion supplements rather than replaces existing components
- Thread pool strategy for pygit2 maintains compatibility
- Progress reporting is central to user experience
- Resource management via semaphores prevents overload
- Gradual rollout enables safe migration

**Ready for implementation**: Start with Phase 1 dependency setup
