# CLAUDE.md - AI Development Companion Guide

> **For Claude Code and other AI development assistants working on Ca-Bhfuil**
>
> **Version**: 3.0 | **Last Updated**: 2025-06-25 | **Compatibility**: Claude Code v1.x, Claude Sonnet 4+

## Project Status

**Ca-Bhfuil** *(pronounced "caw will")* is a git repository analysis tool for open source maintainers, currently in the **core implementation phase**.

**Canonical Repository**: https://github.com/SeanMooney/ca-bhfuil

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
docs/
├── user/                        # User-facing documentation
│   ├── CONTAINER_USAGE.md       # Container usage and security guide
│   └── cli-reference.md         # CLI command reference
├── contributor/                 # Contributor documentation
│   ├── DEVELOPMENT.md           # Development environment setup
│   ├── code-style.md           # Code style guide and standards
│   └── design/                 # Technical design documents
│       ├── project-vision.md            # Product vision and user goals
│       ├── architecture-overview.md     # System design and components
│       ├── technology-decisions.md      # Technology choices and rationale
│       ├── cli-design-patterns.md       # CLI design principles and conventions
│       ├── data-storage-design.md       # Storage architecture and data management
│       ├── repository-management.md     # Git operations and repository management
│       ├── development-workflow.md      # CI/CD and development process
│       └── archive/                     # Previous design documents (archived)
└── README.md                    # Project overview and getting started
```

## Development Workflow

### Before Starting Any Work
1. **Read all files in `ai/memory/`** to understand current project state
2. **Review relevant design documents** for technical context
3. **Read `ai/memory/ai-style-guide.md`** for coding standards and patterns
4. **Update memory files** with any new insights or decisions

### Session Types and Templates

#### Feature Development Session
1. **Read `ai/memory/current-focus.md`** for priorities
2. **Review relevant design docs** in `docs/contributor/design/` for architecture patterns
3. **Check existing tests** for patterns and conventions
4. **Create feature branch**: `feature/descriptive-name`
5. **Implement with TDD approach**: Write failing test first
6. **Update documentation**: User docs (`docs/user/`) and contributor docs as needed
7. **Run quality gates** before commit (see Quality Gates section)
8. **Update memory files** with new patterns or decisions

#### Bug Fix Session
1. **Reproduce issue** with a failing test
2. **Check `ai/memory/architecture-decisions.md`** for relevant context
3. **Implement minimal fix** that addresses root cause
4. **Verify fix doesn't break** existing functionality
5. **Update documentation** if behavior changes
6. **Document any new insights** in memory files

#### Refactoring Session
1. **Document current behavior** with comprehensive tests
2. **Review design documents** for intended patterns
3. **Refactor incrementally** with continuous testing
4. **Update design docs** if architecture changes
5. **Ensure no functionality changes** unless explicitly intended

### AI Assistant Handoff Protocol

#### When Starting a New Session
1. **Read session summary** from previous AI assistant (if exists in current-focus.md)
2. **Check git status** to understand current working state
3. **Review recent commits** to understand what was accomplished: `git log --oneline -10`
4. **Scan memory files** for any updates since last session
5. **Update current-focus.md** with your session goals and planned approach

#### When Ending a Session
1. **Commit all changes** with descriptive messages following project conventions
2. **Update current-focus.md** with:
   - Progress made this session
   - Current status of work
   - Next steps for following AI assistant
   - Any blockers or decisions needed
3. **Document any new patterns** discovered during implementation
4. **Create session summary** if significant work was accomplished
5. **Update relevant memory files** with new insights or decisions

#### Session Handoff Template (add to current-focus.md)
```markdown
## Session Handoff - [Date]
**Completed**: [What was finished this session]  
**In Progress**: [What is partially done]  
**Next Steps**: [Immediate actions for next session]  
**Blockers**: [Issues that need resolution]  
**Key Decisions**: [Important choices made]  
**Files Modified**: [List of changed files]
```

### When Ready to Begin Development
1. **Check `ai/memory/current-focus.md`** for current priorities
2. **Follow tasks in `ai/memory/bootstrap-tasks.md`** for implementation steps
3. **Reference technology decisions** in `docs/contributor/design/technology-decisions.md`
4. **ALWAYS follow coding guidelines** in `ai/memory/ai-style-guide.md`
5. **Update memory files** as you make progress and decisions

### Code Quality Requirements
- **Follow the AI Style Guide**: All code must adhere to `ai/memory/ai-style-guide.md`
- **Module-only imports**: Never import functions/classes directly - only import modules
- **Type hints required**: Use modern Python 3.10+ type syntax throughout
- **Test coverage**: Write comprehensive tests for all new functionality
- **Run quality checks**: `uv run ruff check`, `uv run mypy`, `uv run pytest` before committing

### Quality Gates Checklist

Before committing any code, AI assistants must verify:

#### Code Quality ✅
- [ ] **All tests passing**: `uv run pytest` returns success
- [ ] **Type checking clean**: `uv run mypy` shows no errors
- [ ] **Linting clean**: `uv run ruff check` shows no violations
- [ ] **Formatting applied**: `uv run ruff format` has been run
- [ ] **Import style correct**: Module-only imports used throughout
- [ ] **Type hints present**: All public functions have type annotations

#### Documentation ✅
- [ ] **User docs updated**: `docs/user/` updated for user-facing changes
- [ ] **CLI reference updated**: `docs/user/cli-reference.md` reflects new commands/options
- [ ] **Design docs updated**: `docs/contributor/design/` updated for architectural changes
- [ ] **Code comments added**: Complex logic has explanatory comments
- [ ] **Docstrings present**: All public functions have proper docstrings

#### Memory System ✅
- [ ] **Memory files updated**: Relevant files in `ai/memory/` reflect new insights
- [ ] **Decisions documented**: Architectural choices recorded in `architecture-decisions.md`
- [ ] **Patterns captured**: New successful patterns added to `patterns.md`
- [ ] **Current focus updated**: `current-focus.md` reflects session progress

#### Integration ✅
- [ ] **No breaking changes**: Existing functionality still works
- [ ] **Dependencies appropriate**: Only approved technologies used (see `technology-decisions.md`)
- [ ] **Configuration valid**: Changes don't break existing configurations
- [ ] **Error handling present**: Proper exception handling for new code paths

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
│   ├── user/                  # User documentation ✅
│   │   ├── CONTAINER_USAGE.md # Container usage guide
│   │   └── cli-reference.md   # CLI command reference
│   └── contributor/           # Contributor documentation ✅
│       ├── DEVELOPMENT.md     # Development setup
│       ├── code-style.md      # Code style guide
│       └── design/            # Design documents
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
- ✅ **Git Repository Management Design**: Complete architecture in `docs/contributor/design/repository-management.md`
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
- `ai/memory/ai-style-guide.md` - Keep in sync with `docs/contributor/code-style.md`

### Decision Documentation Framework

When making architectural or technical decisions, document them in `ai/memory/architecture-decisions.md` using this format:

```markdown
## Decision: [Brief Title]
**Date**: YYYY-MM-DD  
**Status**: Proposed | Accepted | Superseded  
**Context**: [What problem are we solving? What constraints exist?]

### Problem
[Describe the problem that necessitates this decision]

### Alternatives Considered
1. **Option A**: [Description] - Pros: [...] Cons: [...]
2. **Option B**: [Description] - Pros: [...] Cons: [...]
3. **Selected Option**: [Description] - Pros: [...] Cons: [...]

### Rationale
[Why this option was chosen over alternatives]

### Impact
- **Performance**: [How this affects system performance]
- **Development**: [How this affects development workflow]
- **Users**: [How this affects end users]
- **Future**: [How this affects future development]

### Implementation Notes
[Key implementation details or constraints]

### Reversibility
[How difficult would this be to change later? What would be required?]
```

### Enhanced Memory Management

#### Session Logs for Complex Work
For substantial development work spanning multiple sessions, create:
`ai/memory/session-logs/YYYY-MM-DD-feature-name.md`

```markdown
# Session Log: [Feature Name]
**Date**: YYYY-MM-DD  
**Objective**: [What we're trying to accomplish]

## Progress Made
- [Key accomplishments this session]
- [Important decisions made]
- [Tests written/passing]

## Challenges Encountered
- [Technical issues and how resolved]
- [Design conflicts and resolutions]
- [Unexpected complexities discovered]

## Key Learnings
- [Patterns that worked well]
- [Anti-patterns to avoid]
- [Insights for future development]

## Next Steps
- [Immediate next actions for following session]
- [Longer-term goals]
- [Dependencies to resolve]

## Code Locations
- [Key files modified]
- [New files created]
- [Test files updated]
```

#### Pattern Library
Maintain `ai/memory/patterns.md` with reusable solutions:

```markdown
# Development Patterns Library

## Code Patterns That Work Well
- [Specific patterns used successfully in this codebase]
- [Testing strategies that have been effective]
- [Error handling approaches that work]

## Anti-Patterns to Avoid
- [Patterns that caused problems]
- [Why they didn't work]
- [Better alternatives]

## Architecture Patterns
- [Higher-level design patterns used]
- [Integration patterns between components]
- [Data flow patterns]
```

### Document New Patterns
- Add development patterns to appropriate memory files
- Update project context when understanding evolves
- Create session logs for complex development work

### Style Guide Synchronization

**CRITICAL**: When `docs/contributor/code-style.md` is updated, `ai/memory/ai-style-guide.md` MUST be updated to maintain an AI-optimized version.

**Process for Style Guide Updates**:
1. **When `docs/contributor/code-style.md` changes**: AI assistant must immediately update `ai/memory/ai-style-guide.md`
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

## Troubleshooting and Recovery

### Common Development Issues

#### When Tests Fail After Changes
1. **Don't commit failing tests** - always fix or mark as known issues first
2. **Check recent changes**: `git diff HEAD~1` to see what might have broken
3. **Run specific test**: `uv run pytest path/to/failing_test.py -v` for details
4. **Check dependencies**: Ensure no version conflicts in `uv.lock`
5. **Review design docs**: Verify changes align with intended architecture
6. **Restore known good state**: `git stash` or `git reset` if needed

#### When Design Conflicts Arise
1. **Document the conflict** in `ai/memory/architecture-decisions.md`
2. **Review existing decisions** for precedent and rationale
3. **Consult design documents** in `docs/contributor/design/` for guidance
4. **Propose solutions** with trade-offs analysis
5. **Update design docs** once resolution is clear
6. **Ensure consistency** across all affected components

#### When Implementation Gets Complex
1. **Step back and review** the original design documents
2. **Break into smaller pieces** - implement incrementally
3. **Write tests first** to clarify expected behavior
4. **Create session log** to track decisions and learnings
5. **Update memory files** with new patterns discovered
6. **Consider if design needs updating** based on new complexity

#### When Dependencies Cause Issues
1. **Check technology decisions** in `docs/contributor/design/technology-decisions.md`
2. **Verify UV lock file**: `uv lock --check` for consistency
3. **Review recent dependency changes**: Check if updates broke something
4. **Use approved dependencies only** - no unauthorized additions
5. **Document new dependencies** in architecture decisions if needed

### Recovery Procedures

#### Recovering from Bad Commits
```bash
# View recent commits
git log --oneline -10

# Soft reset to fix last commit (keeps changes)
git reset --soft HEAD~1

# Hard reset to discard changes completely (dangerous!)
git reset --hard HEAD~1

# Interactive rebase to edit multiple commits
git rebase -i HEAD~3
```

#### Recovering Lost Work
```bash
# Find lost commits
git reflog

# Restore from reflog
git checkout <commit-hash>
git checkout -b recovery-branch

# Restore specific files
git checkout HEAD~1 -- path/to/file
```

#### Cleaning Up Development Environment
```bash
# Clean UV environment
rm -rf .venv
uv sync --dev

# Clean Git status
git clean -fd  # Remove untracked files (careful!)
git reset --hard HEAD  # Reset to last commit
```

## Project Evolution Guidelines

### Technology Updates

When considering updates to dependencies or core technologies:

#### Before Making Changes
1. **Check current rationale** in `docs/contributor/design/technology-decisions.md`
2. **Document the motivation** for the update (security, features, performance)
3. **Assess impact** on existing code and architecture
4. **Create migration plan** with rollback strategy
5. **Test thoroughly** with representative workloads

#### During Updates
1. **Update in stages** - don't change everything at once
2. **Maintain backward compatibility** when possible
3. **Update tests first** to catch regressions
4. **Document breaking changes** clearly
5. **Update AI style guide** for new patterns or requirements

#### After Updates
1. **Update technology decisions** document with new rationale
2. **Update memory files** with new patterns or constraints
3. **Verify all quality gates** still pass
4. **Create migration notes** for future reference

### Feature Deprecation

When removing or replacing features:

#### Planning Phase
1. **Mark as deprecated** with clear timeline in documentation
2. **Provide migration path** or alternatives
3. **Update user documentation** with deprecation notices
4. **Plan removal timeline** (minimum 2 releases recommended)

#### Implementation Phase
1. **Add deprecation warnings** to code
2. **Maintain backward compatibility** during deprecation period
3. **Update tests** to handle deprecated features
4. **Communicate changes** in release notes

#### Removal Phase
1. **Remove deprecated code** after deprecation period
2. **Update documentation** to remove references
3. **Update design documents** if architecture changes
4. **Verify no breaking side effects**

### Architecture Evolution

When making significant architectural changes:

#### Documentation First
1. **Update design documents** before implementing
2. **Document migration strategy** from current to new architecture
3. **Identify breaking changes** and mitigation strategies
4. **Get alignment** on approach before proceeding

#### Incremental Implementation
1. **Implement in phases** to minimize risk
2. **Maintain parallel systems** during transition if needed
3. **Validate each phase** thoroughly before proceeding
4. **Document lessons learned** for future evolutions

## Development Tools Integration

### IDE Configuration

#### Recommended VSCode Settings
Create `.vscode/settings.json` for consistent development environment:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.terminal.activateEnvironment": false,
    "python.linting.enabled": false,
    "python.formatting.provider": "none",
    "editor.formatOnSave": true,
    "editor.rulers": [88],
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {
            "source.organizeImports": true,
            "source.fixAll": true
        }
    },
    "mypy-type-checker.importStrategy": "fromEnvironment",
    "ruff.importStrategy": "fromEnvironment"
}
```

#### Recommended Extensions
- **Python** - Python language support
- **Pylance** - Advanced Python language server
- **Ruff** - Linting and formatting
- **MyPy Type Checker** - Type checking integration
- **GitHub Copilot** - AI code assistance (if available)

### CI/CD Integration

#### Branch Protection Rules
Configure GitHub branch protection for main branches:
- Require pull request reviews
- Require status checks to pass (CI, type checking, linting)
- Require branches to be up to date before merging
- Include administrators in restrictions

#### Automated Testing
Ensure CI validates AI-generated code:
- All quality gates must pass in CI
- Test coverage reporting
- Dependency vulnerability scanning
- Documentation validation

### Git Hooks Integration

#### Pre-commit Configuration
The project uses pre-commit hooks to enforce quality:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run on all files manually
uv run pre-commit run --all-files
```

#### Custom Git Hooks
Consider adding project-specific hooks:
- Commit message validation
- Memory file update reminders
- Documentation sync checks

### Quality Assurance

#### Automated Quality Checks
- **Ruff**: Linting and formatting
- **MyPy**: Type checking in strict mode
- **Pytest**: Comprehensive test suite
- **UV**: Dependency management and security

#### Integration with AI Development
- Quality gates align with AI assistant workflow
- Memory system updates can be validated automatically
- Documentation consistency can be checked in CI

## Questions or Issues?

If you need clarification:
1. **Check AI memory files** for documented decisions
2. **Review design documents** for comprehensive context  
3. **Update memory files** with new insights
4. **Ask specific questions** about unclear requirements
5. **Use troubleshooting section** for common development issues

## 🚨 Critical Reminders for AI Assistants

### Code Quality Standards
- **ALWAYS follow `ai/memory/ai-style-guide.md`** - Non-negotiable coding standards
- **Module-only imports**: Never import functions/classes directly (e.g., use `pathlib.Path`, not `from pathlib import Path`)
- **Type hints required**: Use modern Python 3.10+ syntax (`list[str]` not `List[str]`)
- **Test first**: Write comprehensive tests for all new functionality
- **Quality gates**: Run `uv run ruff check`, `uv run mypy`, `uv run pytest` before any commit

### Documentation Maintenance
- **Follow design guidance**: Always reference existing design documents in `docs/contributor/design/` for consistency
- **Update documentation**: When developing new features, update relevant docs (user docs, design docs, CLI reference)
- **Design-driven development**: Consult architecture and design patterns before implementing new features
- **User vs Contributor docs**: Update user docs (`docs/user/`) for end-user features, contributor docs for development changes

### Style Guide Synchronization
- **When `docs/contributor/code-style.md` changes**: IMMEDIATELY update `ai/memory/ai-style-guide.md`
- **Maintain AI optimization**: Keep the condensed guide focused on patterns AI assistants need most
- **Verify completeness**: Ensure critical patterns from the full guide are captured in the AI version

---

**Ready to build something useful for open source maintainers!** 🚀

*Remember: This tool helps maintainers answer "Cá bhfuil?" (where is?) for their commits across complex git histories.*
