# CLAUDE.md - AI Development Companion Guide

> **For Claude Code and other AI development assistants working on Ca-Bhfuil**

## Project Status

**Ca-Bhfuil** *(pronounced "caw will")* is a git repository analysis tool for open source maintainers, currently in the **core implementation phase**.

- ✅ **Design Complete**: Project vision, technology stack, and architecture defined
- ✅ **Structure Ready**: Repository organization and AI memory system established
- ✅ **Bootstrap Complete**: Python package structure implemented and functional
- 🔄 **Current Phase**: Core functionality development (git operations, search, analysis)
- ⏳ **Next Goal**: Implement git operations using pygit2 and search functionality

## Quick Context

### What This Tool Does
Helps open source maintainers track commits across stable branches:
- Find where CVE fixes have been backported
- Identify what's missing from stable branches
- Understand commit distribution across git history

### Key Technical Decisions
- **Git Operations**: pygit2 (LibGit2 bindings) for 10x+ performance
- **Storage**: SQLite-based everything (diskcache + custom schemas)
- **AI Integration**: Local-first (Ollama/vLLM) with optional cloud fallback
- **CLI**: Typer with Rich terminal output
- **Philosophy**: Local-first, privacy-preserving, single-developer optimized

## AI Memory System

This project uses **file-based AI memory** for persistent context across development sessions.

### Essential Reading (Read These First)
```
ai/memory/
├── project-context.md          # High-level project understanding
├── architecture-decisions.md   # Key technical decisions
├── current-focus.md           # Active development priorities
└── bootstrap-tasks.md         # Specific development tasks
```

### Complete Documentation
```
docs/design/
├── project-vision.md          # Complete technical vision and user workflows
├── technology-stack.md        # All technology decisions with rationale
└── repository-structure.md    # Full development organization guide
```

## Development Workflow

### Before Starting Any Work
1. **Read all files in `ai/memory/`** to understand current project state
2. **Review relevant design documents** for technical context
3. **Update memory files** with any new insights or decisions

### When Ready to Begin Development
1. **Check `ai/memory/current-focus.md`** for current priorities
2. **Follow tasks in `ai/memory/bootstrap-tasks.md`** for implementation steps
3. **Reference technology stack** in `docs/design/technology-stack.md`
4. **Update memory files** as you make progress and decisions

## Repository Structure (Current)

```
ca-bhfuil/
├── src/ca_bhfuil/             # Main application package ✅
│   ├── cli/                   # Command-line interface (Typer) ✅
│   │   └── main.py           # CLI implementation with typer
│   ├── core/                  # Core business logic ✅
│   │   ├── git/              # Git operations (pygit2) 🔄
│   │   ├── models/           # Pydantic data models ✅
│   │   │   └── commit.py     # CommitInfo model
│   │   ├── search/           # Search implementations 🔄
│   │   ├── analysis/         # Analysis algorithms 🔄
│   │   └── config.py         # Configuration management ✅
│   ├── storage/              # SQLite-based persistence ✅
│   │   ├── cache/            # Caching (diskcache) ✅
│   │   │   └── diskcache_wrapper.py
│   │   └── database/         # Database operations ✅
│   │       └── schema.py     # Database schema
│   ├── agents/               # AI integration (PydanticAI) 🔄
│   ├── integrations/         # External integrations 🔄
│   └── utils/                # Utilities 🔄
├── tests/                     # Test suite ✅
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test fixtures
├── docs/                      # Documentation ✅
├── ai/                        # AI development workspace ✅
├── scripts/                   # Development utilities ✅
├── config/                    # Configuration templates ✅
├── pyproject.toml            # Package configuration ✅
└── uv.lock                   # Dependency lock file ✅
```

**Legend**: ✅ Implemented | 🔄 In Progress | ⏳ Planned

## Key Development Principles

### Performance First
- Use pygit2 for all git operations (never GitPython)
- Implement aggressive caching from day one
- Design for repositories with 10k+ commits

### Local-First Everything
- All storage uses SQLite (no external databases)
- AI models run locally when possible
- No required external services

### Type Safety
- Full type hints throughout codebase
- Pydantic models for all data structures
- mypy strict mode configuration

### AI Integration
- Provider-agnostic design (Ollama, vLLM, OpenRouter)
- Local models preferred, cloud optional
- Structured output using Pydantic schemas

## Current Implementation Status

The repository has completed the bootstrap phase and is ready for core functionality development.

### Completed Bootstrap Items
- ✅ Python package structure implemented
- ✅ CLI framework functional with Typer
- ✅ Configuration management with Pydantic settings
- ✅ Storage layer foundation (SQLite + diskcache)
- ✅ Basic data models (CommitInfo)
- ✅ Package can be installed and CLI runs
- ✅ Development tooling configured (ruff, mypy, pytest)

### Next Development Phase
Focus on implementing core git operations and search functionality:

```
Implement git repository operations using pygit2, starting with 
basic repository detection, commit lookup, and branch analysis.
Then add search capabilities for SHA and commit message patterns.
```

## Memory Management

### Always Update These Files
- `ai/memory/current-focus.md` - What you're actively working on
- `ai/memory/architecture-decisions.md` - Any new technical decisions
- `ai/memory/bootstrap-tasks.md` - Progress on development tasks

### Document New Patterns
- Add development patterns to appropriate memory files
- Update project context when understanding evolves
- Create session logs for complex development work

## Questions or Issues?

If you need clarification:
1. **Check AI memory files** for documented decisions
2. **Review design documents** for comprehensive context  
3. **Update memory files** with new insights
4. **Ask specific questions** about unclear requirements

---

**Ready to build something useful for open source maintainers!** 🚀

*Remember: This tool helps maintainers answer "Cá bhfuil?" (where is?) for their commits across complex git histories.*