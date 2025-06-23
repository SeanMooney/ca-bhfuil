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
3. **Read `ai/memory/ai-style-guide.md`** for coding standards and patterns
4. **Update memory files** with any new insights or decisions

### When Ready to Begin Development
1. **Check `ai/memory/current-focus.md`** for current priorities
2. **Follow tasks in `ai/memory/bootstrap-tasks.md`** for implementation steps
3. **Reference technology stack** in `docs/design/technology-stack.md`
4. **ALWAYS follow coding guidelines** in `ai/memory/ai-style-guide.md`
5. **Update memory files** as you make progress and decisions

### Code Quality Requirements
- **Follow the AI Style Guide**: All code must adhere to `ai/memory/ai-style-guide.md`
- **Module-only imports**: Never import functions/classes directly - only import modules
- **Type hints required**: Use modern Python 3.10+ type syntax throughout
- **Test coverage**: Write comprehensive tests for all new functionality
- **Run quality checks**: `uv run ruff check`, `uv run mypy`, `uv run pytest` before committing

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

**DESIGN PHASE COMPLETE** ✅ - Ready for core implementation

### Completed Phases
- ✅ **Bootstrap Phase**: Python package structure, CLI framework, basic tooling
- ✅ **Design Phase**: Complete git repository management architecture

### Design Phase Achievements (2025-01-21)
- ✅ **Git Repository Management Design**: Complete architecture in `docs/design/git-repository-management.md`
- ✅ **XDG Base Directory Compliance**: Linux standards-compliant data storage
- ✅ **Security Architecture**: SSH-first authentication with separate config files
- ✅ **CLI Pattern**: Consistent `ca-bhfuil <resource> <operation> [--options]` interface
- ✅ **Concurrent Safety**: Lock file management for safe operations
- ✅ **Schema Versioning**: Future-proof SQLite database design

### Current Architecture Summary

**Directory Structure (XDG Compliant)**:
```
~/.config/ca-bhfuil/          # Configuration (git-safe)
├── repositories.yaml         # Repository definitions
├── global-settings.yaml      # Global settings  
└── auth.yaml                 # Authentication (git-ignored)

~/.local/state/ca-bhfuil/     # Persistent state (important data)
└── github.com/torvalds/linux/# Metadata per repository
    ├── analysis.db           # Commit analysis
    ├── sync-log.db          # Sync history
    └── .locks/              # Concurrent operation safety

~/.cache/ca-bhfuil/          # Cache data (can be regenerated)
└── repos/github.com/torvalds/linux/  # Git repositories
```

**Key Design Decisions**:
- URL-based repository organization (no slugs)
- SSH-preferred authentication
- SQLite with schema versioning
- pygit2 for high-performance git operations

### Next Implementation Phase

**Priority 1: Configuration Foundation**
```
Implement XDG-compliant configuration management system with URL-to-path
utilities and authentication handling as the foundation for all other functionality.
```

**Priority 2: Git Operations Core**  
```
Implement repository registry and basic git operations using pygit2 for
repository detection, commit lookup, and synchronization.
```

## Memory Management

### Always Update These Files
- `ai/memory/current-focus.md` - What you're actively working on
- `ai/memory/architecture-decisions.md` - Any new technical decisions
- `ai/memory/bootstrap-tasks.md` - Progress on development tasks
- `ai/memory/ai-style-guide.md` - Keep in sync with `docs/code-style.md`

### Document New Patterns
- Add development patterns to appropriate memory files
- Update project context when understanding evolves
- Create session logs for complex development work

### Style Guide Synchronization

**CRITICAL**: When `docs/code-style.md` is updated, `ai/memory/ai-style-guide.md` MUST be updated to maintain an AI-optimized version.

**Process for Style Guide Updates**:
1. **When `docs/code-style.md` changes**: AI assistant must immediately update `ai/memory/ai-style-guide.md`
2. **AI-optimized format**: Create condensed, actionable guidelines focused on patterns AI assistants need
3. **Key differences**: AI guide emphasizes import patterns, type hints, and critical anti-patterns
4. **Bidirectional sync**: Changes to coding practices should be reflected in both files
5. **Validation**: AI should verify the condensed guide captures all critical patterns from the full guide

**Essential AI Style Guide Elements**:
- Module-only import patterns (CRITICAL)
- Type hint requirements and modern syntax
- Error handling patterns
- Testing structure and mocking guidelines
- Common anti-patterns to avoid
- Quick reference examples for immediate use

## Questions or Issues?

If you need clarification:
1. **Check AI memory files** for documented decisions
2. **Review design documents** for comprehensive context  
3. **Update memory files** with new insights
4. **Ask specific questions** about unclear requirements

## 🚨 Critical Reminders for AI Assistants

### Code Quality Standards
- **ALWAYS follow `ai/memory/ai-style-guide.md`** - Non-negotiable coding standards
- **Module-only imports**: Never import functions/classes directly (e.g., use `pathlib.Path`, not `from pathlib import Path`)
- **Type hints required**: Use modern Python 3.10+ syntax (`list[str]` not `List[str]`)
- **Test first**: Write comprehensive tests for all new functionality
- **Quality gates**: Run `uv run ruff check`, `uv run mypy`, `uv run pytest` before any commit

### Style Guide Synchronization
- **When `docs/code-style.md` changes**: IMMEDIATELY update `ai/memory/ai-style-guide.md`
- **Maintain AI optimization**: Keep the condensed guide focused on patterns AI assistants need most
- **Verify completeness**: Ensure critical patterns from the full guide are captured in the AI version

---

**Ready to build something useful for open source maintainers!** 🚀

*Remember: This tool helps maintainers answer "Cá bhfuil?" (where is?) for their commits across complex git histories.*
