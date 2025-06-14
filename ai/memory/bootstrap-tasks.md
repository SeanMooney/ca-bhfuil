# Bootstrap Development Tasks

## Overview
Specific development tasks for Claude Code to implement the ca-bhfuil Python package, broken down into manageable phases with clear success criteria.

## Phase 1: Package Foundation (Priority 1)

### Task 1.1: Create Python Package Structure
**Estimated Effort**: 30 minutes  
**Dependencies**: None

Create the basic Python package directory structure:
```bash
mkdir -p src/ca_bhfuil/{cli,core/{git,models,search,analysis},storage/{cache,database},agents,integrations,utils}
touch src/ca_bhfuil/{__init__.py,__main__.py,py.typed}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p {scripts,config}
```

**Success Criteria**:
- [ ] Package structure matches repository-structure.md design
- [ ] All required `__init__.py` files present
- [ ] `py.typed` marker file for type checking

### Task 1.2: Create pyproject.toml
**Estimated Effort**: 45 minutes  
**Dependencies**: Task 1.1

Create `pyproject.toml` with dependencies from technology-stack.md:
- Core dependencies: pygit2, diskcache, httpx, pydantic-settings, typer, loguru
- Development dependencies: pytest, ruff, mypy, pre-commit
- Project metadata and build configuration
- Tool configurations for ruff and mypy

**Success Criteria**:
- [ ] `pip install -e .` installs without errors
- [ ] All core dependencies from tech stack included
- [ ] Development tools configured properly

### Task 1.3: Create .gitignore and Basic Config
**Estimated Effort**: 15 minutes  
**Dependencies**: None

Create comprehensive `.gitignore` for Python + ca-bhfuil specific exclusions.

**Success Criteria**:
- [ ] Python artifacts excluded
- [ ] Ca-bhfuil cache directories excluded (.ca-bhfuil/)
- [ ] AI session logs excluded (ai/session-logs/)
- [ ] Development artifacts excluded

## Phase 2: Core Infrastructure (Priority 2)

### Task 2.1: Basic Package Initialization
**Estimated Effort**: 30 minutes  
**Dependencies**: Task 1.1, 1.2

Implement basic package files:
- `src/ca_bhfuil/__init__.py` with version and core exports
- `src/ca_bhfuil/__main__.py` as CLI entry point
- Basic error handling and logging setup

**Success Criteria**:
- [ ] Package imports successfully
- [ ] `python -m ca_bhfuil` runs without error
- [ ] Version information accessible

### Task 2.2: Configuration Management
**Estimated Effort**: 1 hour  
**Dependencies**: Task 2.1

Implement configuration system using pydantic-settings:
- Application settings with defaults
- Environment variable support
- YAML configuration file support
- Cache directory management

**Success Criteria**:
- [ ] Configuration loads from environment variables
- [ ] YAML configuration file support working
- [ ] Cache directory created automatically
- [ ] Settings validation with Pydantic

### Task 2.3: Basic Storage Layer
**Estimated Effort**: 1.5 hours  
**Dependencies**: Task 2.2

Implement SQLite-based storage foundation:
- `storage/cache/diskcache_wrapper.py` using diskcache
- `storage/database/schema.py` with basic database schema
- Cache directory structure creation
- Basic cache operations (get, set, clear)

**Success Criteria**:
- [ ] Cache manager initializes correctly
- [ ] SQLite cache files created in proper location
- [ ] Basic cache operations work
- [ ] Cache persistence across application restarts

## Phase 3: CLI Framework (Priority 3)

### Task 3.1: Basic CLI Application
**Estimated Effort**: 1 hour  
**Dependencies**: Task 2.1

Implement basic Typer CLI application:
- `cli/main.py` with Typer app setup
- Basic commands: `search`, `status`, `--help`
- Rich console output configuration
- Error handling and user feedback

**Success Criteria**:
- [ ] `ca-bhfuil --help` shows proper help
- [ ] Basic commands respond correctly
- [ ] Rich output formatting works
- [ ] Error messages are user-friendly

### Task 3.2: Command Structure
**Estimated Effort**: 45 minutes  
**Dependencies**: Task 3.1

Create command structure and basic implementations:
- Command for repository analysis status
- Command for basic commit search (placeholder)
- Global options (verbose, repo path)
- Command help and examples

**Success Criteria**:
- [ ] Commands have proper help text
- [ ] Repository path detection works
- [ ] Verbose output option functional
- [ ] Commands fail gracefully with clear messages

## Phase 4: Git Operations Foundation (Priority 4)

### Task 4.1: Pydantic Models
**Estimated Effort**: 1 hour  
**Dependencies**: Task 2.1

Create core data models:
- `core/models/commit.py` with CommitInfo model
- `core/models/branch.py` with branch-related models
- Models include proper type hints and validation
- JSON serialization support

**Success Criteria**:
- [ ] Models serialize/deserialize correctly
- [ ] Type validation works properly
- [ ] Models integrate with storage layer
- [ ] Documentation strings complete

### Task 4.2: Basic Git Repository Wrapper
**Estimated Effort**: 2 hours  
**Dependencies**: Task 4.1, Task 2.3

Implement basic git operations using pygit2:
- `core/git/repository.py` with Repository class
- Basic repository detection and initialization
- Simple commit retrieval by SHA
- Branch and tag listing
- Integration with cache layer

**Success Criteria**:
- [ ] Repository class initializes with pygit2
- [ ] Can find git repository from any subdirectory
- [ ] Basic commit lookup by SHA works
- [ ] Branch and tag listing functional
- [ ] Results cached appropriately

### Task 4.3: Basic Search Implementation
**Estimated Effort**: 1.5 hours  
**Dependencies**: Task 4.2

Implement basic commit search:
- Search by full or partial SHA
- Simple pattern matching for commit messages
- Integration with CLI search command
- Basic result formatting

**Success Criteria**:
- [ ] SHA search returns correct commits
- [ ] Partial SHA matching works
- [ ] Search results display properly in CLI
- [ ] Search operations are cached

## Phase 5: Testing and Quality (Priority 5)

### Task 5.1: Basic Test Suite
**Estimated Effort**: 1.5 hours  
**Dependencies**: All previous tasks

Create basic test coverage:
- `tests/conftest.py` with pytest configuration
- Unit tests for core models
- Integration tests for git operations
- Test fixtures for sample repositories

**Success Criteria**:
- [ ] pytest runs without errors
- [ ] Core functionality has test coverage
- [ ] Test fixtures support different scenarios
- [ ] Tests run in isolation

### Task 5.2: Development Tooling Setup
**Estimated Effort**: 45 minutes  
**Dependencies**: Task 1.2

Configure development tools:
- Pre-commit hooks configuration
- Ruff linting and formatting
- mypy type checking
- GitHub Actions workflow (basic)

**Success Criteria**:
- [ ] `ruff check` passes
- [ ] `mypy` type checking passes
- [ ] Pre-commit hooks install and run
- [ ] All tools have proper configuration

## Success Criteria for Complete Bootstrap

The bootstrap phase is complete when:

- [ ] **Installation**: `pip install -e .` works without errors
- [ ] **CLI**: `ca-bhfuil --help` shows proper help output
- [ ] **Basic Function**: `ca-bhfuil search <sha>` finds commits in local git repo
- [ ] **Storage**: SQLite caching operational and persistent
- [ ] **Quality**: All development tools (ruff, mypy) pass
- [ ] **Testing**: Basic test suite runs successfully
- [ ] **Documentation**: Installation and usage instructions updated

## Post-Bootstrap Priorities

After bootstrap completion, focus should shift to:
1. Enhanced search capabilities (Change-ID, issue references)
2. Branch distribution analysis
3. AI integration setup
4. Rich terminal output improvements
5. Issue tracker integration

## Notes for Claude Code

- **Follow technology stack strictly** - use only dependencies listed in docs/design/technology-stack.md
- **Implement incrementally** - each task should result in working, testable code
- **Update memory files** - document decisions and progress in ai/memory/
- **Focus on fundamentals** - get basic functionality solid before adding features
- **Test continuously** - ensure each phase works before moving to next

Remember: The goal is a solid foundation, not a complete application. Build incrementally and prioritize reliability over features.