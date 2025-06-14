# PLANNING.md - Ca-Bhfuil Restructure Implementation Plan

## Overview

This document provides a detailed implementation plan for restructuring ca-bhfuil from a LangChain/LangGraph proof-of-concept to a production-ready tool using PydanticAI and FastMCP. This plan is designed to be executed by Claude Code or similar AI coding assistants.

## Project Context

**Current State**: ca-bhfuil is a proof-of-concept using LangChain and LangGraph for git repository analysis
**Target State**: Production-ready tool using PydanticAI agents and FastMCP for standardized LLM integration
**Goal**: Create a comprehensive git analysis tool that can locate patches, commits, and provide intelligent summaries

## Implementation Tasks

### TASK 1: Project Structure Setup
**Priority**: HIGH
**Estimated Effort**: 1-2 hours

#### Subtasks:
1. **Create new project structure** using modern Python best practices
2. **Initialize uv project** with proper configuration
3. **Set up development tooling** (ruff, mypy, pytest, pre-commit)
4. **Create GitHub workflows** for CI/CD

#### Files to Create:
```
├── pyproject.toml              # Main project configuration
├── .gitignore                  # Git ignore patterns
├── .dockerignore               # Docker ignore patterns
├── README.md                   # Updated project documentation
├── LICENSE                     # MIT license
├── Dockerfile                  # Container configuration
├── .github/workflows/
│   ├── ci.yml                  # Testing and linting
│   ├── release.yml             # PyPI publishing
│   └── docker.yml              # Container builds
├── .pre-commit-config.yaml     # Pre-commit hooks
└── scripts/
    ├── setup_dev.sh            # Development setup script
    └── build_container.sh      # Container build script
```

#### Key Requirements:
- Use `src/` layout for package structure
- Configure uv for dependency management
- Set up ruff for linting and formatting
- Configure mypy for type checking
- Set up pytest with async support

### TASK 2: Core Data Models
**Priority**: HIGH
**Estimated Effort**: 2-3 hours

#### Subtasks:
1. **Define Pydantic models** for all git-related data structures
2. **Create configuration models** for application settings
3. **Implement validation logic** for git data
4. **Add custom exceptions** for error handling

#### Files to Create:
```
src/ca_bhfuil/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── models.py               # Pydantic data models
│   ├── config.py               # Configuration management
│   └── exceptions.py           # Custom exceptions
```

#### Required Models:
- `CommitInfo`: Git commit data with validation
- `BranchInfo`: Branch metadata and commit lists
- `TagInfo`: Git tag information
- `SearchResult`: Search operation results
- `CommitAnalysis`: AI analysis results
- `RepositoryConfig`: Repository configuration
- `AppConfig`: Application-wide settings

### TASK 3: Git Operations Layer
**Priority**: HIGH
**Estimated Effort**: 3-4 hours

#### Subtasks:
1. **Implement GitRepository class** for git operations
2. **Create search functionality** for commits, change IDs, and patches
3. **Add branch and tag analysis** capabilities
4. **Implement async git operations** for performance

#### Files to Create:
```
src/ca_bhfuil/git/
├── __init__.py
├── repository.py               # Main GitRepository class
├── analysis.py                 # Git analysis logic
├── search.py                   # Search implementations
└── utils.py                    # Git utilities and helpers
```

#### Required Functionality:
- Search commits by SHA, change ID, title, author
- Analyze commit impact and relationships
- Find branches/tags containing specific commits
- Extract metadata from commit messages
- Support for Gerrit change IDs and other trackers

### TASK 4: PydanticAI Agents
**Priority**: HIGH
**Estimated Effort**: 3-4 hours

#### Subtasks:
1. **Create search agent** for finding commits and patches
2. **Implement analysis agent** for commit analysis
3. **Add summarization agent** for generating reports
4. **Configure agent tools** with proper typing

#### Files to Create:
```
src/ca_bhfuil/core/
└── agents.py                   # PydanticAI agent definitions
```

#### Required Agents:
- `search_agent`: Find commits by various criteria
- `analysis_agent`: Analyze commit purpose and impact
- `summary_agent`: Generate human-readable summaries
- Agent tools for git operations
- Dependency injection for repository access

### TASK 5: FastMCP Server Implementation
**Priority**: HIGH
**Estimated Effort**: 2-3 hours

#### Subtasks:
1. **Create MCP server** with FastMCP framework
2. **Implement MCP tools** for git operations
3. **Add MCP resources** for repository metadata
4. **Define MCP prompts** for common analysis patterns

#### Files to Create:
```
src/ca_bhfuil/mcp/
├── __init__.py
├── server.py                   # Main FastMCP server
├── tools.py                    # MCP tools for git operations
├── resources.py                # MCP resources for data
└── prompts.py                  # MCP prompts and templates
```

#### Required MCP Components:
- Tools: `find_commit`, `analyze_commit`, `search_branches`
- Resources: `repo_info`, `branch_list`, `tag_list`
- Prompts: `analyze_patch`, `find_related`, `summarize_changes`

### TASK 6: CLI Interface
**Priority**: MEDIUM
**Estimated Effort**: 2-3 hours

#### Subtasks:
1. **Create CLI application** using Typer
2. **Implement rich output** with tables and formatting
3. **Add multiple output formats** (JSON, table, markdown)
4. **Configure command structure** with subcommands

#### Files to Create:
```
src/ca_bhfuil/
├── __main__.py                 # CLI entry point
└── cli/
    ├── __init__.py
    ├── main.py                 # Main CLI application
    ├── commands.py             # CLI command implementations
    └── utils.py                # CLI utilities
```

#### Required Commands:
- `search`: Find commits by various criteria
- `analyze`: Analyze specific commits
- `branches`: List and analyze branches
- `tags`: List and analyze tags
- `summary`: Generate repository summaries

### TASK 7: Standalone Interface
**Priority**: LOW
**Estimated Effort**: 1-2 hours

#### Subtasks:
1. **Create simple prompt loop** for standalone usage
2. **Implement basic conversation flow** with agents
3. **Add help and command suggestions**

#### Files to Create:
```
src/ca_bhfuil/standalone/
├── __init__.py
├── loop.py                     # Simple prompt loop
└── interface.py                # Standalone interface
```

### TASK 8: Testing Infrastructure
**Priority**: MEDIUM
**Estimated Effort**: 3-4 hours

#### Subtasks:
1. **Set up pytest configuration** with async support
2. **Create test fixtures** for git repositories
3. **Implement unit tests** for all modules
4. **Add integration tests** for agent workflows

#### Files to Create:
```
tests/
├── __init__.py
├── conftest.py                 # pytest configuration
├── fixtures/                   # Test data and fixtures
├── test_core/
│   ├── test_agents.py
│   ├── test_models.py
│   └── test_config.py
├── test_git/
│   ├── test_repository.py
│   ├── test_analysis.py
│   └── test_search.py
├── test_mcp/
│   ├── test_server.py
│   ├── test_tools.py
│   └── test_resources.py
└── test_cli/
    ├── test_main.py
    └── test_commands.py
```

### TASK 9: Documentation and Examples
**Priority**: MEDIUM
**Estimated Effort**: 2-3 hours

#### Subtasks:
1. **Create comprehensive README** with usage examples
2. **Write API documentation** for all modules
3. **Add usage examples** for different scenarios
4. **Create MCP integration guide**

#### Files to Create:
```
docs/
├── index.md                    # Main documentation
├── installation.md             # Installation guide
├── usage.md                    # Usage examples
├── mcp-integration.md          # MCP setup guide
└── api.md                      # API reference

examples/
├── basic_usage.py              # Basic CLI usage
├── mcp_server_example.py       # MCP server setup
├── claude_desktop_config.json  # Claude Desktop config
└── advanced_analysis.py        # Advanced use cases
```

### TASK 10: Container and Deployment
**Priority**: LOW
**Estimated Effort**: 1-2 hours

#### Subtasks:
1. **Create Dockerfile** for containerized deployment
2. **Set up GitHub Actions** for automated builds
3. **Configure PyPI publishing** workflow

## Implementation Order

### Phase 1: Foundation (Tasks 1-3)
Execute in order: Project Setup → Data Models → Git Operations
**Timeline**: 1-2 days
**Dependencies**: None

### Phase 2: Core Functionality (Tasks 4-5)
Execute in parallel: PydanticAI Agents + FastMCP Server
**Timeline**: 1 day
**Dependencies**: Phase 1 complete

### Phase 3: Interfaces (Tasks 6-7)
Execute in parallel: CLI + Standalone Interface
**Timeline**: 1 day
**Dependencies**: Phase 2 complete

### Phase 4: Quality & Deployment (Tasks 8-10)
Execute in parallel: Testing + Documentation + Deployment
**Timeline**: 1-2 days
**Dependencies**: Phase 3 complete

## Technical Specifications

### Dependencies
```toml
# Core dependencies
pydantic-ai = ">=0.1.0"
fastmcp = ">=2.0.0"
typer = {extras = ["all"], version = ">=0.12.0"}
rich = ">=13.0.0"
gitpython = ">=3.1.0"
aiofiles = ">=24.0.0"
httpx = ">=0.27.0"

# Development dependencies
pytest = ">=8.0.0"
pytest-asyncio = ">=0.24.0"
pytest-cov = ">=4.0.0"
ruff = ">=0.6.0"
mypy = ">=1.8.0"
pre-commit = ">=3.0.0"
```

### Python Version Support
- Minimum: Python 3.10
- Recommended: Python 3.11+
- Type hints: Full type annotation coverage

### Code Quality Standards
- **Linting**: Ruff with strict configuration
- **Type Checking**: mypy with strict mode
- **Testing**: 90%+ test coverage
- **Documentation**: Docstrings for all public APIs

## Migration Notes

### From LangChain/LangGraph
- Replace StateGraph with PydanticAI Agent classes
- Convert LangChain tools to PydanticAI tools with proper typing
- Replace memory/state management with dependency injection
- Migrate prompts to PydanticAI system prompts

### New Features with FastMCP
- Standardized tool interface for LLM integration
- Resource-based data access patterns
- Prompt templates for common operations
- Easy integration with Claude Desktop and other MCP clients

## Success Criteria

1. **Functional**: All original ca-bhfuil functionality preserved and enhanced
2. **Performance**: Faster startup and execution vs LangChain version
3. **Integration**: Successful MCP integration with Claude Desktop
4. **Quality**: 90%+ test coverage, type safety, proper error handling
5. **Usability**: Intuitive CLI interface with rich output formatting
6. **Deployment**: Container packaging and PyPI distribution working

## Risk Mitigation

- **Dependency Issues**: Pin versions and test with multiple Python versions
- **Migration Complexity**: Implement incrementally with feature parity checks
- **Performance**: Profile and optimize critical paths
- **Integration**: Test MCP server with multiple clients
- **Maintenance**: Comprehensive documentation and examples

## Implementation Notes for Claude Code

1. **Start with Task 1** (Project Structure) - this provides the foundation
2. **Follow the phased approach** - don't skip to later phases without completing dependencies
3. **Maintain backward compatibility** during migration where possible
4. **Test each component** as it's implemented
5. **Use type hints extensively** - they're critical for PydanticAI
6. **Follow the existing code patterns** from the original ca-bhfuil where applicable
7. **Implement async/await properly** - required for PydanticAI and FastMCP
8. **Keep security in mind** - validate all inputs and handle errors gracefully

## File Generation Priority

### Critical Path Files (implement first):
1. `pyproject.toml` - Project configuration
2. `src/ca_bhfuil/core/models.py` - Data models
3. `src/ca_bhfuil/git/repository.py` - Git operations
4. `src/ca_bhfuil/core/agents.py` - PydanticAI agents
5. `src/ca_bhfuil/mcp/server.py` - FastMCP server

### Supporting Files (implement after critical path):
6. `src/ca_bhfuil/cli/main.py` - CLI interface
7. `tests/conftest.py` - Test configuration
8. `README.md` - Documentation
9. `Dockerfile` - Container setup
10. `.github/workflows/ci.yml` - CI/CD pipeline