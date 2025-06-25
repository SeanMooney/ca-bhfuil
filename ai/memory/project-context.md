# Project Context

> **High-level project understanding for AI assistants**
>
> **Last Updated**: 2025-06-27

## What is Ca-Bhfuil?

**Ca-Bhfuil** *(pronounced "caw will")* is a git repository analysis tool designed for open source maintainers. The name means "where is?" in Irish, reflecting the tool's purpose of helping maintainers locate commits across complex git histories.

## Core Problem

Open source maintainers need to track commits across multiple stable branches:
- Find where CVE fixes have been backported
- Identify what's missing from stable branches  
- Understand commit distribution across git history
- Track security patches and critical fixes

## Solution Approach

A local-first, high-performance tool that:
- Uses pygit2 for 10x+ performance over GitPython
- Stores everything locally with SQLite
- Provides rich CLI interface with Typer
- Integrates optional AI analysis capabilities
- Maintains privacy with local-only operations

## Current Development Phase

**Status**: Core implementation phase
- ✅ Design complete with comprehensive architecture
- ✅ Bootstrap complete with Python package structure
- ✅ Configuration foundation implemented
- 🔄 Repository management and git operations (current focus)

## Key Architectural Principles

1. **Local-First**: All operations work offline with local SQLite storage
2. **Performance-Focused**: Designed for repositories with 10k+ commits
3. **Privacy-Preserving**: No required external services or data sharing
4. **AI-Enhanced**: Optional local AI integration for commit analysis
5. **Standards-Compliant**: XDG Base Directory compliance on Linux

## Technology Foundation

- **Git Operations**: pygit2 (LibGit2 bindings) for performance
- **Storage**: SQLite with diskcache for everything
- **CLI**: Typer with Rich for beautiful terminal output
- **AI Integration**: PydanticAI with local models (Ollama/vLLM)
- **Configuration**: Pydantic v2 with YAML files

## User Workflow

1. **Configure repositories**: Add git repositories to track
2. **Sync and analyze**: Download/update repositories and analyze commits
3. **Search and query**: Find commits by SHA, pattern, or semantic meaning
4. **Cross-reference**: Understand commit relationships across branches
5. **Generate reports**: Export findings for documentation or further analysis

## Success Metrics

- **Performance**: Sub-second search in 10k+ commit repositories
- **Usability**: Intuitive CLI that matches maintainer mental models
- **Reliability**: Handles large repositories without memory issues
- **Privacy**: Zero external dependencies for core functionality

## Authoritative Documentation

For detailed information, see:
- **Project vision**: `docs/contributor/design/project-vision.md`
- **Architecture**: `docs/contributor/design/architecture-overview.md`
- **Technology decisions**: `docs/contributor/design/technology-decisions.md`
- **Development workflow**: `docs/contributor/design/development-workflow.md`

## Key Development Decisions

Refer to `ai/memory/architecture-decisions.md` for detailed ADRs on:
- XDG Base Directory compliance
- URL-based repository organization
- SQLite schema versioning
- pygit2 for git operations
- Local-first storage strategy

---

This context provides the foundation for understanding ca-bhfuil's purpose and approach. Refer to authoritative documentation for implementation details.
