# TECH-STACK.md - Ca-Bhfuil Technology Stack (Refined for Performance)

## Overview

This document defines the optimized technology stack for ca-bhfuil, a git repository analysis tool that tracks changes across branches and understands relationships between commits and external issue trackers. This version is refined for large repositories (10k+ commits), single-developer workflow, and flexible deployment scenarios.

**License**: MIT License  
**Philosophy**: High performance, minimal dependencies, aggressive caching, single-developer friendly  
**Optimization Target**: Large open-source projects with extensive commit history

## Refined Technical Decisions

### Key Changes from Initial Design:
- **Git Library**: pygit2 (LibGit2 bindings) for superior performance on large repositories
- **Caching Strategy**: Aggressive disk-based caching with configurable TTLs
- **Issue Tracker Pattern**: Lazy loading with link rendering, fetch content only when requested
- **Development Workflow**: Single-developer optimized with comprehensive pre-commit automation
- **Deployment**: Local CLI + remotely deployable MCP server with persistent storage

## Core Technology Stack

### AI/Agent Framework

#### PydanticAI (MIT)
- **Purpose**: Primary AI agent framework for LLM integration
- **Why Chosen**: Type-safe agent definitions with dependency injection, better than LangChain for structured workflows
- **Used For**: Search agents, analysis agents, commit summarization
- **Key Benefits**: Runtime type validation, clean dependency management, async-first design
- **Documentation**: [PydanticAI Docs](https://ai.pydantic.dev/)

#### FastMCP (MIT)
- **Purpose**: Model Context Protocol server implementation
- **Why Chosen**: Standardized interface for LLM tool integration, enables Claude Desktop integration
- **Used For**: Exposing git analysis tools to LLMs, remote agent deployment
- **Key Benefits**: Protocol standardization, easy LLM client integration, tool discovery
- **Documentation**: [FastMCP GitHub](https://github.com/jlowin/fastmcp)

### High-Performance Git Analysis

#### pygit2 (GPL-2.0 with linking exception)
- **Purpose**: Primary git repository interface
- **Why Chosen**: LibGit2 bindings provide 10x+ performance improvement over GitPython for large repositories
- **Used For**: All git operations - commit retrieval, branch analysis, file diff analysis
- **Key Benefits**: Memory efficiency, speed on large repos, robust git implementation
- **Trade-offs**: More complex installation (requires libgit2), less Pythonic API than GitPython
- **Documentation**: [pygit2 Documentation](https://www.pygit2.org/)
- **Installation Guide**: [LibGit2 Installation](https://github.com/libgit2/pygit2#installation)

#### diskcache (Apache-2.0)
- **Purpose**: Persistent caching for git operations and API responses
- **Why Chosen**: Pure Python implementation, thread-safe, automatic eviction, SQLite backend
- **Used For**: Caching commit data, API responses, search results, branch analysis
- **Key Benefits**: Persistence across runs, automatic size management, fast lookups
- **Alternative Considered**: Redis (rejected due to external dependency complexity)
- **Documentation**: [DiskCache Documentation](http://www.grantjenks.com/docs/diskcache/)

### Issue Tracker Integration (Lazy Loading)

#### httpx (BSD-3-Clause)
- **Purpose**: Unified HTTP client for all external API calls
- **Why Chosen**: Async-first design, HTTP/2 support, connection pooling, better than requests for async workloads
- **Used For**: JIRA REST API, GitHub API, Launchpad API calls
- **Key Benefits**: Connection reuse, timeout handling, automatic retries
- **Documentation**: [HTTPX Documentation](https://www.python-httpx.org/)

#### regex (Apache-2.0)
- **Purpose**: Enhanced pattern matching for issue ID extraction
- **Why Chosen**: More powerful than stdlib `re`, better Unicode support, advanced features
- **Used For**: Extracting JIRA issue IDs, GitHub issue references, Gerrit change IDs from commit messages
- **Key Benefits**: Better performance, more regex features, backward compatibility with `re`
- **Documentation**: [Regex Documentation](https://github.com/mrabarnett/mrab-regex)

### Issue Tracker Strategy
- **Approach**: Lazy loading with aggressive caching
- **Implementation**: Render clickable links immediately, fetch content only when explicitly requested
- **Benefit**: Reduces API rate limiting, improves response times, minimizes unnecessary network calls
- **Supported Trackers**: JIRA (REST API), GitHub (REST API), Launchpad (REST API)

### Configuration Management

#### pydantic-settings[yaml] (MIT)
- **Purpose**: Type-safe configuration with multiple sources
- **Why Chosen**: Integrates with Pydantic models, supports YAML + environment variables, validation
- **Used For**: Application configuration, cache settings, tracker credentials, deployment config
- **Key Benefits**: Type validation, environment override, YAML readability
- **Documentation**: [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

#### python-dotenv (BSD-3-Clause)
- **Purpose**: Environment variable loading from .env files
- **Why Chosen**: Standard approach for local development environment management
- **Used For**: Loading API tokens, development overrides, local configuration
- **Documentation**: [Python-dotenv](https://github.com/theskumar/python-dotenv)

### Terminal Interface

#### typer[all] (MIT)
- **Purpose**: CLI framework with automatic help generation and type hints
- **Why Chosen**: Built on click, automatic help generation, Rich integration included, type-safe
- **Used For**: Main CLI interface, command parsing, help system
- **Key Benefits**: Type safety, automatic completion, Rich terminal output included
- **Documentation**: [Typer Documentation](https://typer.tiangolo.com/)

#### prompt-toolkit (BSD-3-Clause)
- **Purpose**: Advanced interactive terminal features
- **Why Chosen**: Powerful completion system, history, syntax highlighting for interactive mode
- **Used For**: Interactive REPL mode, command completion, input validation
- **Key Benefits**: Rich interactive experience, cross-platform compatibility
- **Documentation**: [Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/)

### Logging

#### loguru (MIT)
- **Purpose**: Modern logging with structured output and Rich integration
- **Why Chosen**: Simpler than stdlib logging, JSON serialization, automatic Rich formatting
- **Used For**: Application logging, performance metrics, error tracking
- **Key Benefits**: Easy configuration, structured logging, beautiful terminal output
- **Documentation**: [Loguru Documentation](https://loguru.readthedocs.io/)

### Utilities

#### aiofiles (Apache-2.0)
- **Purpose**: Async file operations
- **Why Chosen**: Non-blocking file I/O for large repository analysis
- **Used For**: Reading large git objects, configuration files, cache files
- **Documentation**: [aiofiles](https://github.com/Tinche/aiofiles)

## Dependencies Structure

### Core Dependencies (8 total)
Essential dependencies for basic functionality:
- **pydantic-ai**: AI agent framework
- **fastmcp**: MCP server implementation  
- **pygit2**: High-performance git operations
- **httpx**: HTTP client for APIs
- **diskcache**: Persistent caching
- **pydantic-settings[yaml]**: Configuration management
- **typer[all]**: CLI framework (includes Rich)
- **loguru**: Logging

### Enhanced Dependencies (3 total)
Additional utilities for full functionality:
- **prompt-toolkit**: Interactive features
- **python-dotenv**: Environment variables
- **aiofiles**: Async file operations
- **regex**: Enhanced pattern matching

### Optional Dependencies
Available as extras for specific use cases:
- **advanced-analysis**: pydriller for complex git analysis
- **text-processing**: nltk for natural language processing

### Development Dependencies
Single-developer optimized tooling:
- **pytest + pytest-asyncio**: Testing framework
- **ruff**: All-in-one linting and formatting (replaces black, flake8, isort)
- **mypy**: Type checking
- **pre-commit**: Automated code quality

## Architecture Benefits

### Performance Optimizations
- **pygit2**: 10x+ speed improvement over GitPython for large repositories
- **Aggressive Caching**: Disk-based persistence reduces repeated git operations
- **Lazy Loading**: Issue tracker content fetched only when needed
- **Connection Pooling**: httpx reuses connections for API efficiency

### Development Efficiency
- **Type Safety**: Pydantic models throughout ensure runtime validation
- **Single Tool**: Ruff handles all linting/formatting needs
- **Pre-commit Automation**: Quality checks run automatically
- **Rich Terminal Output**: Better debugging and user experience

### Deployment Flexibility
- **Local CLI**: Direct command-line usage for development
- **MCP Server**: Remote deployment with persistent caching
- **Container Ready**: Docker support with volume mounts for cache persistence
- **Kubernetes Compatible**: Persistent volume claims for cache storage

### Operational Benefits
- **Minimal Dependencies**: Only 11 core dependencies reduces maintenance overhead
- **Persistent Caching**: Survives application restarts, improves cold start performance
- **Health Monitoring**: Built-in health checks for deployed MCP servers
- **Configuration Flexibility**: YAML + environment variables support multiple deployment scenarios

## Dependency Rationale

### Why pygit2 over GitPython
- **Performance**: LibGit2 is optimized C library, much faster for large repositories
- **Memory Usage**: More efficient memory handling for large commit histories
- **Robustness**: Battle-tested git implementation used by many tools
- **Trade-off**: More complex installation, requires system libgit2

### Why diskcache over Redis
- **Simplicity**: No external service dependency
- **Persistence**: Automatic cache persistence without configuration
- **Single Developer**: Reduces operational complexity
- **Performance**: Fast enough for local and small-scale remote deployments

### Why httpx over requests
- **Async Support**: Native async/await support for non-blocking API calls
- **HTTP/2**: Better performance for repeated API calls
- **Connection Pooling**: Automatic connection reuse
- **Modern Design**: Built for current Python async patterns

### Why ruff over multiple tools
- **Single Tool**: Replaces black, flake8, isort, pyupgrade
- **Speed**: Written in Rust, much faster than Python alternatives
- **Configuration**: Single configuration file
- **Maintenance**: Reduces tool dependency management

## External Resources

### Git Performance
- [LibGit2 Performance Comparison](https://github.com/libgit2/libgit2#performance)
- [pygit2 vs GitPython Benchmarks](https://www.pygit2.org/recipes/git-performance.html)

### Caching Strategies
- [DiskCache Performance Guide](http://www.grantjenks.com/docs/diskcache/tutorial.html#performance)
- [Python Caching Patterns](https://realpython.com/python-caching/)

### MCP Protocol
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Claude Desktop MCP Integration](https://docs.anthropic.com/en/docs/build-with-claude/computer-use)

### Deployment Guides
- [FastAPI Deployment Best Practices](https://fastapi.tiangolo.com/deployment/) (similar patterns apply to FastMCP)
- [Python Container Optimization](https://pythonspeed.com/docker/)

This stack provides optimal performance for large repository analysis while maintaining simplicity for single-developer workflow and flexible deployment options.
