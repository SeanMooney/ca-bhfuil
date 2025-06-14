# REPO-STRUCTURE.md - Ca-Bhfuil Repository Organization

## Overview

This document defines the repository structure for ca-bhfuil, optimized for both human developers and AI contributors (particularly Claude Code). Following our local-first philosophy, the structure uses file-based storage for AI memory, planning, and collaboration across development sessions.

**Design Principles**:
- **Human-First**: Clear, logical organization for traditional development
- **AI-Accessible**: File-based memory system for persistent AI collaboration
- **Local Storage**: No external dependencies for development memory/state
- **Session Persistence**: AI context survives across multiple development sessions
- **Self-Documenting**: Structure itself communicates project organization

## Root Directory Structure

```
ca-bhfuil/
├── README.md                    # Project overview and quick start
├── CLAUDE.md                    # AI development companion guide
├── pyproject.toml              # Python packaging and dependencies
├── Dockerfile                  # Container deployment
├── .gitignore                  # Version control exclusions
├── .pre-commit-config.yaml     # Development quality automation
│
├── docs/                       # Human-readable documentation
├── src/                        # Application source code
├── tests/                      # Test suite
├── scripts/                    # Development and deployment utilities
├── config/                     # Configuration templates and examples
├── ai/                         # AI development workspace (file-based memory)
└── .ca-bhfuil/                 # Local development cache (git-ignored)
```

## Core Application Structure

### `src/ca_bhfuil/` - Main Application

```
src/ca_bhfuil/
├── __init__.py                 # Package initialization
├── __main__.py                 # CLI entry point
├── cli/                        # Command-line interface
├── core/                       # Core business logic
├── agents/                     # AI agent implementations
├── storage/                    # Local data persistence
├── integrations/              # External service connectors
├── utils/                      # Shared utilities
└── py.typed                    # Type checking marker
```

#### `src/ca_bhfuil/cli/` - User Interface Layer

```
cli/
├── __init__.py
├── main.py                     # Primary CLI application (Typer)
├── commands/                   # Command implementations
│   ├── __init__.py
│   ├── search.py              # Search operations
│   ├── analyze.py             # Analysis commands
│   ├── backport.py            # Backport workflows
│   └── interactive.py         # Interactive REPL mode
├── output/                     # Output formatting
│   ├── __init__.py
│   ├── formatters.py          # Rich terminal formatting
│   ├── tables.py              # Tabular output
│   └── reports.py             # Report generation
└── config/                     # CLI configuration
    ├── __init__.py
    └── settings.py            # CLI-specific settings
```

#### `src/ca_bhfuil/core/` - Business Logic

```
core/
├── __init__.py
├── models/                     # Pydantic data models
│   ├── __init__.py
│   ├── commit.py              # Git commit representations
│   ├── branch.py              # Branch and tag models
│   ├── tracker.py             # Issue tracker models
│   └── analysis.py            # Analysis result models
├── git/                        # Git repository operations
│   ├── __init__.py
│   ├── repository.py          # pygit2 repository wrapper
│   ├── commit_finder.py       # Commit search algorithms
│   ├── branch_analyzer.py     # Branch comparison logic
│   └── change_tracker.py      # Change ID tracking
├── search/                     # Search implementations
│   ├── __init__.py
│   ├── engines.py             # Search engine interfaces
│   ├── patterns.py            # Pattern matching (regex)
│   ├── semantic.py            # AI-powered semantic search
│   └── filters.py             # Search result filtering
└── analysis/                   # Analysis algorithms
    ├── __init__.py
    ├── backport.py            # Backport detection
    ├── distribution.py        # Branch distribution analysis
    ├── classification.py      # Change classification
    └── relationships.py       # Commit relationship mapping
```

#### `src/ca_bhfuil/agents/` - AI Integration Layer

```
agents/
├── __init__.py
├── base.py                     # PydanticAI base agent definitions
├── providers/                  # AI provider implementations
│   ├── __init__.py
│   ├── ollama.py              # Ollama local models
│   ├── openrouter.py          # OpenRouter cloud models
│   ├── vllm.py                # vLLM inference server
│   └── lmstudio.py            # LMStudio local models
├── tasks/                      # Specialized AI tasks
│   ├── __init__.py
│   ├── summarization.py       # Commit summarization
│   ├── classification.py      # Change type classification
│   ├── extraction.py          # Information extraction
│   └── search.py              # Semantic search enhancement
├── embeddings/                 # RAG and vector operations
│   ├── __init__.py
│   ├── generator.py           # Embedding generation
│   ├── storage.py             # SQLite vector storage
│   └── retrieval.py           # Semantic retrieval
└── prompts/                    # Structured prompts
    ├── __init__.py
    ├── templates.py           # Prompt templates
    └── schemas.py             # Output schemas
```

#### `src/ca_bhfuil/storage/` - Local Persistence

```
storage/
├── __init__.py
├── cache/                      # Caching implementations
│   ├── __init__.py
│   ├── diskcache_wrapper.py   # diskcache integration
│   ├── sqlite_cache.py        # SQLite-based caching
│   └── memory.py              # In-memory fallback
├── database/                   # SQLite database operations
│   ├── __init__.py
│   ├── schema.py              # Database schema definitions
│   ├── migrations.py          # Schema migrations
│   ├── queries.py             # Common queries
│   └── connection.py          # Connection management
├── vectors/                    # RAG vector storage
│   ├── __init__.py
│   ├── sqlite_vec.py          # sqlite-vec integration
│   ├── embeddings.py          # Embedding storage
│   └── search.py              # Vector search operations
└── files/                      # File-based storage utilities
    ├── __init__.py
    ├── config.py              # Configuration file handling
    └── exports.py             # Data export utilities
```

#### `src/ca_bhfuil/integrations/` - External Services

```
integrations/
├── __init__.py
├── trackers/                   # Issue tracker clients
│   ├── __init__.py
│   ├── base.py                # Base tracker interface
│   ├── github.py              # GitHub Issues API
│   ├── jira.py                # JIRA REST API
│   ├── launchpad.py           # Launchpad API
│   └── patterns.py            # Issue ID extraction patterns
├── mcp/                        # Model Context Protocol server
│   ├── __init__.py
│   ├── server.py              # FastMCP server implementation
│   ├── tools.py               # MCP tool definitions
│   └── schemas.py             # MCP schema definitions
└── ci/                         # CI/CD integrations
    ├── __init__.py
    ├── github_actions.py      # GitHub Actions integration
    └── generic_webhooks.py    # Generic webhook handlers
```

## AI Development Workspace

### `ai/` - File-Based AI Memory System

The `ai/` directory provides persistent, file-based memory for AI development sessions, allowing Claude Code and other AI assistants to maintain context across multiple sessions.

```
ai/
├── README.md                   # AI workspace documentation
├── memory/                     # Session-persistent AI memory
├── analysis/                   # Code and design analysis
├── planning/                   # Development planning documents
├── tasks/                      # Task tracking and management
├── reference/                  # Quick reference materials
├── experiments/                # Experimental ideas and prototypes
└── session-logs/              # Development session history
```

#### `ai/memory/` - Persistent AI Context

```
memory/
├── project-context.md         # High-level project understanding
├── architecture-decisions.md  # Technical decision rationale
├── current-focus.md           # Active development areas
├── known-issues.md            # Tracked problems and limitations
├── next-steps.md              # Immediate development priorities
├── code-patterns.md           # Established coding patterns
├── dependencies.md            # Library and tool decisions
└── user-feedback.md           # User requirements and feedback
```

#### `ai/analysis/` - Development Analysis

```
analysis/
├── codebase-review/           # Code quality and structure analysis
│   ├── current-state.md      # Current codebase assessment
│   ├── refactoring-needs.md  # Identified refactoring opportunities
│   └── technical-debt.md     # Technical debt tracking
├── performance/               # Performance analysis
│   ├── bottlenecks.md        # Identified performance issues
│   ├── optimization-ideas.md # Performance improvement strategies
│   └── benchmarks.md         # Performance measurement results
├── security/                  # Security considerations
│   ├── threat-model.md       # Security threat analysis
│   ├── vulnerabilities.md    # Known security issues
│   └── mitigations.md        # Security improvement plans
└── compatibility/             # Compatibility analysis
    ├── python-versions.md    # Python version compatibility
    ├── os-support.md         # Operating system support
    └── dependency-conflicts.md # Dependency compatibility issues
```

#### `ai/planning/` - Development Planning

```
planning/
├── features/                  # Feature development plans
│   ├── current-sprint.md     # Active feature development
│   ├── next-features.md      # Planned feature additions
│   └── feature-backlog.md    # Future feature ideas
├── architecture/             # Architectural planning
│   ├── design-evolution.md   # Architectural evolution plans
│   ├── integration-points.md # External integration planning
│   └── scalability.md        # Scalability considerations
├── releases/                  # Release planning
│   ├── version-roadmap.md    # Release version planning
│   ├── breaking-changes.md   # Breaking change management
│   └── migration-guides.md   # User migration assistance
└── infrastructure/            # Infrastructure planning
    ├── deployment.md         # Deployment strategy evolution
    ├── testing.md            # Testing strategy improvements
    └── documentation.md      # Documentation enhancement plans
```

#### `ai/tasks/` - Task Management

```
tasks/
├── active/                    # Currently active tasks
│   ├── implementation/       # Implementation tasks
│   ├── testing/              # Testing tasks
│   ├── documentation/        # Documentation tasks
│   └── debugging/            # Bug fixing tasks
├── completed/                 # Completed task history
│   ├── 2025-06/             # Monthly completion archives
│   └── README.md            # Completed task index
├── blocked/                   # Blocked or postponed tasks
│   ├── technical-blocks.md   # Technically blocked tasks
│   ├── decision-needed.md    # Tasks awaiting decisions
│   └── external-deps.md      # Tasks blocked by external dependencies
└── ideas/                     # Task ideas and proposals
    ├── improvements.md       # Improvement suggestions
    ├── new-features.md       # New feature task ideas
    └── research.md           # Research task proposals
```

#### `ai/reference/` - Quick Reference

```
reference/
├── api-patterns.md           # Common API usage patterns
├── testing-patterns.md       # Testing approach patterns
├── git-workflows.md          # Git workflow references
├── cli-design.md             # CLI design principles
├── performance-tips.md       # Performance optimization tips
├── debugging-guide.md        # Debugging methodology
├── code-style.md            # Code style guidelines
└── external-resources.md     # External documentation links
```

#### `ai/experiments/` - Experimental Development

```
experiments/
├── prototypes/               # Code prototypes and experiments
│   ├── performance-tests/   # Performance testing experiments
│   ├── ui-experiments/      # User interface experiments
│   └── algorithm-tests/     # Algorithm implementation tests
├── research/                 # Research and investigation
│   ├── competitive-analysis.md # Similar tool analysis
│   ├── technology-research.md  # Technology evaluation
│   └── user-research.md        # User needs research
└── ideas/                    # Experimental ideas
    ├── feature-concepts.md   # Feature concept exploration
    ├── architecture-ideas.md # Architecture experiment ideas
    └── integration-concepts.md # Integration experiment ideas
```

#### `ai/session-logs/` - Development Session History

```
session-logs/
├── 2025-06/                  # Monthly session logs
│   ├── 2025-06-14-initial-setup.md
│   ├── 2025-06-15-core-implementation.md
│   └── README.md            # Monthly session index
├── templates/                # Session log templates
│   ├── development-session.md
│   ├── debugging-session.md
│   └── planning-session.md
└── summaries/                # Session summary reports
    ├── weekly-summaries/    # Weekly development summaries
    └── milestone-summaries/ # Milestone completion summaries
```

## Documentation Structure

### `docs/` - Human Documentation

```
docs/
├── README.md                 # Documentation index
├── user-guide/               # End-user documentation
│   ├── installation.md      # Installation instructions
│   ├── quick-start.md        # Getting started guide
│   ├── commands.md           # CLI command reference
│   ├── examples.md           # Usage examples
│   └── troubleshooting.md    # Common issues and solutions
├── developer-guide/          # Developer documentation
│   ├── contributing.md       # Contribution guidelines
│   ├── development-setup.md  # Development environment setup
│   ├── architecture.md       # Technical architecture
│   ├── api-reference.md      # Code API documentation
│   └── testing.md            # Testing guidelines
├── ai-integration/           # AI-specific documentation
│   ├── claude-code-setup.md  # Claude Code integration guide
│   ├── ai-workflow.md        # AI-assisted development workflow
│   └── memory-system.md      # AI memory system documentation
└── deployment/               # Deployment documentation
    ├── local-deployment.md   # Local installation and usage
    ├── mcp-server.md         # MCP server deployment
    └── docker.md             # Container deployment
```

## Testing Structure

### `tests/` - Test Suite Organization

```
tests/
├── conftest.py               # pytest configuration and fixtures
├── unit/                     # Unit tests
│   ├── test_core/           # Core business logic tests
│   ├── test_agents/         # AI agent tests
│   ├── test_storage/        # Storage layer tests
│   └── test_integrations/   # Integration tests
├── integration/              # Integration tests
│   ├── test_git_operations/ # Git operation integration tests
│   ├── test_ai_workflow/    # AI workflow integration tests
│   └── test_cli_commands/   # CLI command integration tests
├── performance/              # Performance tests
│   ├── test_large_repos/    # Large repository performance tests
│   ├── test_cache_efficiency/ # Cache performance tests
│   └── benchmarks/          # Performance benchmarks
├── fixtures/                 # Test data and fixtures
│   ├── sample_repos/        # Sample git repositories
│   ├── mock_responses/      # Mock API responses
│   └── test_configs/        # Test configuration files
└── ai/                       # AI-specific tests
    ├── test_prompts/        # Prompt effectiveness tests
    ├── test_providers/      # AI provider integration tests
    └── test_embeddings/     # Embedding generation tests
```

## Configuration and Scripts

### `config/` - Configuration Templates

```
config/
├── README.md                 # Configuration documentation
├── examples/                 # Example configurations
│   ├── local-development.yaml
│   ├── production-mcp.yaml
│   └── ai-providers.yaml
├── schemas/                  # Configuration schemas
│   ├── app-config.schema.json
│   └── ai-config.schema.json
└── templates/                # Configuration templates
    ├── .env.template
    └── ca-bhfuil.yaml.template
```

### `scripts/` - Development Utilities

```
scripts/
├── setup/                    # Setup and installation scripts
│   ├── install-dependencies.sh
│   ├── setup-dev-environment.sh
│   └── configure-pre-commit.sh
├── development/              # Development workflow scripts
│   ├── run-tests.sh
│   ├── lint-and-format.sh
│   ├── generate-docs.sh
│   └── performance-benchmark.sh
├── deployment/               # Deployment scripts
│   ├── build-container.sh
│   ├── deploy-mcp-server.sh
│   └── release-preparation.sh
└── ai/                       # AI development scripts
    ├── setup-claude-code.sh
    ├── backup-ai-memory.sh
    └── generate-session-summary.sh
```

## Local Development Cache

### `.ca-bhfuil/` - Local Cache (Git-Ignored)

```
.ca-bhfuil/                   # Local development cache (in .gitignore)
├── cache/                    # Application cache
│   ├── repositories/        # Repository analysis cache
│   ├── embeddings/          # AI embedding cache
│   └── api-responses/       # Issue tracker API cache
├── logs/                     # Application logs
│   ├── development.log
│   └── ai-interactions.log
├── temp/                     # Temporary files
└── user-config/              # User-specific configuration
    ├── preferences.yaml
    └── credentials.env
```

## File Naming Conventions

### General Conventions
- **Python modules**: `snake_case.py`
- **Documentation**: `kebab-case.md`
- **Configuration**: `kebab-case.yaml` or `snake_case.env`
- **AI memory files**: `kebab-case.md`
- **Test files**: `test_snake_case.py`

### AI Memory File Conventions
- **Status files**: Present tense (`current-focus.md`, `known-issues.md`)
- **Historical files**: Past tense (`completed-tasks.md`, `decisions-made.md`)
- **Planning files**: Future tense (`next-steps.md`, `planned-features.md`)
- **Session logs**: Date-prefixed (`2025-06-14-session.md`)

## Git Integration

### `.gitignore` Strategy

```gitignore
# Local development cache
.ca-bhfuil/

# AI session logs (optional - team decision)
ai/session-logs/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Local configuration
.env
config/local-*.yaml
```

### AI Memory in Version Control

**Included in Git**:
- `ai/memory/` - Project context and decisions
- `ai/analysis/` - Code analysis results
- `ai/planning/` - Development plans
- `ai/reference/` - Reference materials
- `ai/experiments/` - Experimental results

**Excluded from Git**:
- `ai/session-logs/` - Personal development sessions
- `.ca-bhfuil/` - Local cache and temporary files

## Benefits of This Structure

### For Human Developers
- **Clear Organization**: Logical separation of concerns
- **Self-Documenting**: Structure communicates project organization
- **Standard Patterns**: Follows Python packaging conventions
- **Development Efficiency**: Quick navigation to relevant code

### For AI Contributors
- **Persistent Memory**: File-based memory survives sessions
- **Context Preservation**: Rich context for development decisions
- **Collaborative Planning**: Shared planning and analysis documents
- **Learning System**: AI can build understanding over time

### For Project Maintenance
- **Local-First**: No external dependencies for development memory
- **Version Controlled**: Important context preserved in git history
- **Searchable**: Text-based memory enables easy searching
- **Scalable**: Structure grows with project complexity

### For Community Adoption
- **Accessible**: Standard structure familiar to Python developers
- **Documented**: Comprehensive documentation for new contributors
- **AI-Friendly**: Modern development workflow supporting AI assistance
- **Transparent**: Clear separation between code, documentation, and AI memory

This repository structure enables effective collaboration between human developers and AI assistants while maintaining the simplicity and local-first philosophy of the ca-bhfuil project.