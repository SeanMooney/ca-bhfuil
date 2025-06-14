# PLANNING.md - Ca-Bhfuil Restructure Implementation Plan (Updated)

## Overview

This document provides a detailed implementation plan for restructuring ca-bhfuil from a LangChain/LangGraph proof-of-concept to a production-ready tool using PydanticAI and FastMCP. This plan reflects the refined tech stack decisions optimized for large repositories, single-developer workflow, and flexible deployment.

## Project Context

**Current State**: ca-bhfuil is a proof-of-concept using LangChain and LangGraph for git repository analysis
**Target State**: Production-ready tool using PydanticAI agents and FastMCP for standardized LLM integration
**Optimization Focus**: Large repositories (10k+ commits), minimal operational overhead, single-developer friendly

## Refined Technical Decisions

### Core Changes from Initial Plan:
- **Git Library**: pygit2 instead of GitPython for large repository performance
- **Issue Tracker Strategy**: Lazy loading with link rendering, fetch only when requested
- **Caching**: Aggressive disk-based caching for both git operations and API responses
- **Development Workflow**: Single-developer optimized with comprehensive pre-commit hooks
- **Deployment**: Local CLI + remotely deployable MCP server with persistent storage

## Implementation Tasks

### TASK 1: Project Structure Setup
**Priority**: HIGH
**Estimated Effort**: 1-2 hours

#### Subtasks:
1. **Create new project structure** using modern Python best practices
2. **Initialize uv project** with refined dependency configuration
3. **Set up single-developer tooling** (ruff, mypy, pytest, pre-commit)
4. **Create deployment configurations** for local and remote MCP server

#### Files to Create:
```
├── pyproject.toml              # Updated with pygit2 and refined deps
├── .gitignore                  # Git ignore patterns
├── .dockerignore               # Docker ignore patterns
├── README.md                   # Updated project documentation
├── LICENSE                     # MIT license
├── Dockerfile                  # Multi-stage build for MCP server
├── docker-compose.yml          # Local development and remote deployment
├── .pre-commit-config.yaml     # Comprehensive but simple pre-commit hooks
├── ca-bhfuil.yaml             # Default configuration with caching settings
└── scripts/
    ├── setup_dev.sh            # Development setup script
    ├── build_container.sh      # Container build script
    └── deploy_mcp.sh           # MCP server deployment script
```

#### Key Requirements:
- Use `src/` layout for package structure
- Configure uv with refined dependencies (pygit2, diskcache)
- Set up ruff for all-in-one linting and formatting
- Configure mypy for strict type checking
- Set up pytest with async support and caching tests

#### Updated Dependencies Configuration:
```toml
[project]
dependencies = [
    # Core AI/Agent Framework
    "pydantic-ai>=0.1.0",
    "fastmcp>=2.0.0",
    
    # High-Performance Git Analysis
    "pygit2>=1.13.0",
    
    # HTTP/API with caching
    "httpx>=0.27.0",
    "diskcache>=5.6.0",
    
    # Configuration
    "pydantic-settings[yaml]>=2.9.1",
    "python-dotenv>=1.0.0",
    
    # Terminal Interface
    "typer[all]>=0.12.0",
    "prompt-toolkit>=3.0.51",
    
    # Logging
    "loguru>=0.7.2",
    
    # Utilities
    "aiofiles>=24.0.0",
    "regex>=2023.0.0",
]

[project.optional-dependencies]
advanced-analysis = [
    "pydriller>=2.6",
]

text-processing = [
    "nltk>=3.9",
]

dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0", 
    "pytest-cov>=4.0.0",
    "ruff>=0.6.0",
    "mypy>=1.8.0",
    "pre-commit>=3.0.0",
]
```

### TASK 2: Core Data Models and Configuration
**Priority**: HIGH
**Estimated Effort**: 2-3 hours

#### Subtasks:
1. **Define Pydantic models** for all git-related data structures
2. **Create unified configuration model** with caching and performance settings
3. **Implement validation logic** for git data and configuration
4. **Add custom exceptions** for error handling
5. **Create caching wrapper** for consistent cache usage

#### Files to Create:
```
src/ca_bhfuil/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── models.py               # All Pydantic data models
│   ├── config.py               # Unified configuration management
│   ├── cache.py                # Caching wrapper for git and API data
│   └── exceptions.py           # Custom exceptions
```

#### Required Models:
```python
# models.py structure
@dataclass
class CommitInfo:
    sha: str
    message: str
    author: str
    date: datetime
    parents: List[str]
    files_changed: List[str]
    issue_links: List[str] = field(default_factory=list)  # Rendered links

@dataclass 
class SearchResult:
    commits: List[CommitInfo]
    total_found: int
    search_query: str
    execution_time: float
    cached: bool

@dataclass
class IssueReference:
    id: str
    tracker: str
    url: str
    fetched: bool = False
    content: Optional[Dict] = None  # Only populated when fetched

# config.py structure
class GitConfig(BaseModel):
    cache_enabled: bool = True
    cache_ttl: int = 3600
    max_commits_per_search: int = 10000
    
class TrackerConfig(BaseModel):
    lazy_fetch: bool = True
    cache_ttl: int = 86400  # 24 hours
    jira_url: str = ""
    github_url: str = "https://github.com"
    launchpad_url: str = "https://launchpad.net"

class CacheConfig(BaseModel):
    directory: Path = Path.home() / ".cache" / "ca-bhfuil"
    max_size_mb: int = 1000
    git_ttl: int = 3600
    api_ttl: int = 86400
```

### TASK 3: High-Performance Git Operations Layer
**Priority**: HIGH
**Estimated Effort**: 3-4 hours

#### Subtasks:
1. **Implement GitRepository class** using pygit2 for performance
2. **Create cached search functionality** for commits, change IDs, and patches
3. **Add branch and tag analysis** with caching
4. **Implement async git operations** with proper error handling
5. **Add issue ID extraction** with regex patterns

#### Files to Create:
```
src/ca_bhfuil/git/
├── __init__.py
├── repository.py               # Main GitRepository class using pygit2
├── analysis.py                 # Git analysis logic with caching
├── search.py                   # Optimized search implementations
├── patterns.py                 # Issue ID extraction patterns
└── utils.py                    # Git utilities and helpers
```

#### Required Functionality:
```python
# repository.py key methods
class GitRepository:
    def __init__(self, path: str, cache: Cache):
        self.repo = pygit2.Repository(path)
        self.cache = cache
    
    async def search_commits_by_sha(self, sha: str) -> List[CommitInfo]:
        """Fast SHA search with caching"""
        
    async def search_commits_by_message(self, query: str) ->