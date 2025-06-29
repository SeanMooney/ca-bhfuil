# CLAUDE.md - AI Development Companion Guide

> **For Claude Code and other AI development assistants working on Ca-Bhfuil**
>
> **Version**: 3.1 | **Last Updated**: 2025-06-29 | **Compatibility**: Claude Code v1.x, Claude Sonnet 4+

## Project Status

**For current project status and implementation progress, see `ai/memory/project-status.md`**

**Quick Summary**: Ca-Bhfuil is a git repository analysis tool in the core implementation phase, with configuration foundation complete and ready for repository management implementation.

## Quick Context

**For detailed project understanding, see `ai/memory/project-context.md`**

### What This Tool Does
Helps open source maintainers track commits across stable branches and find where fixes have been backported.

 ### Key Technical Approach
- **High Performance**: pygit2 for git operations
- **Local-First**: SQLite-based storage with no external dependencies
- **AI-Enhanced**: Optional local AI integration
- **Rich CLI**: Typer with beautiful terminal output

**For complete technology rationale, see `docs/contributor/design/technology-decisions.md`**

## AI Memory System

This project uses **file-based AI memory** for persistent context across development sessions.

### Essential AI Memory Files (Read These First)
```
ai/memory/
├── project-context.md          # High-level project understanding
├── architecture-decisions.md   # Key technical decisions (ADR format)
├── current-focus.md           # Active development priorities
├── bootstrap-tasks.md         # Specific development tasks
├── ai-style-guide.md          # Condensed coding standards
└── patterns.md                # Reusable development patterns
```

### Authoritative Documentation Sources
```
docs/contributor/design/        # Complete technical documentation
├── project-vision.md           # Product vision and user goals
├── architecture-overview.md    # System design and components  
├── technology-decisions.md     # Technology choices and rationale
├── repository-management.md    # Git operations design
└── development-workflow.md     # CI/CD and development process
docs/user/                      # User-facing documentation
└── cli-reference.md            # CLI command reference
```

**Key Principle**: AI memory files contain session-specific context. For authoritative project information, always reference `docs/` first.

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
- **Automated quality tools**: Use `uv run ruff check --fix`, `uv run ruff format`, `uv run mypy`, `uv run pytest` before committing
- **Auto-fix enabled**: Ruff will automatically fix most style issues - let it run first

### 🚨 CRITICAL: 100% Pass Rate Required
- **All tests MUST pass**: `uv run pytest` must show 100% success rate (no failing tests)
- **All pre-commit hooks MUST pass**: `uv run pre-commit run --all-files` must show all hooks passing
- **Zero tolerance for failures**: Fix ALL issues before committing - no exceptions
- **Blocking requirement**: Commits with test failures or pre-commit violations are NOT acceptable

### Quality Gates Checklist

Before committing any code, AI assistants must verify:

#### Code Quality ✅
- [ ] **All tests passing**: `uv run pytest` returns 100% success (no failing tests)
- [ ] **Pre-commit hooks passing**: `uv run pre-commit run --all-files` shows all hooks passing
- [ ] **Type checking clean**: `uv run mypy` shows no errors
- [ ] **Auto-fixes applied**: `uv run ruff check --fix` has been run
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

## Repository Structure Reference

**For current repository structure and implementation status, see `ai/memory/bootstrap-tasks.md`**

**Key directories for AI development**:
- `src/ca_bhfuil/`: Main application package
- `tests/`: Comprehensive test suite
- `ai/memory/`: AI session memory and context
- `docs/contributor/design/`: Authoritative design documents

## Key Development Principles

**For complete principles and rationale, see `docs/contributor/design/technology-decisions.md`**

### Core Principles for AI Development
- **Performance First**: Use pygit2, implement aggressive caching
- **Local-First**: SQLite storage, no external dependencies
- **Type Safety**: Full type hints, Pydantic models, mypy strict mode
- **AI Integration**: Local models preferred, structured output

### AI-Specific Development Guidelines
- Always follow `ai/memory/ai-style-guide.md` for coding standards
- Reference `ai/memory/patterns.md` for established development patterns
- Update memory files with new decisions and learnings
- Use session templates for consistent development approach

## Implementation Status Reference

**For current implementation status, see `ai/memory/project-status.md`**
**For detailed current work, see `ai/memory/current-focus.md`**
**For specific development tasks, see `ai/memory/bootstrap-tasks.md`**

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
For substantial development work, create session logs:
`ai/memory/session-logs/YYYY-MM-DD-feature-name.md`

**Template available in session handoff section above.**

#### Pattern Library
**Maintain `ai/memory/patterns.md`** with:
- Code patterns that work well
- Anti-patterns to avoid  
- Architecture and integration patterns
- Testing strategies

#### Best Practices
- **Document new patterns** in appropriate memory files
- **Update project context** when understanding evolves
- **Create session logs** for complex development work
- **Reference authoritative sources** rather than duplicating information

### Style Guide Synchronization

**CRITICAL**: When `docs/contributor/code-style.md` is updated, `ai/memory/ai-style-guide.md` MUST be updated immediately.

**Sync Process**:
1. **Detect changes** in full style guide
2. **Update AI-optimized version** with condensed, actionable guidelines
3. **Validate completeness** - ensure critical patterns are captured
4. **Test compliance** - verify code follows updated standards

**Key Elements in AI Guide**:
- Module-only import patterns (CRITICAL)
- Type hints and modern Python syntax
- Error handling and testing patterns
- Quick reference anti-patterns

## Troubleshooting and Recovery

### Quick Recovery Commands
```bash
# View recent changes
git log --oneline -10
git diff HEAD~1

# Fix broken environment  
rm -rf .venv && uv sync --dev

# Run quality checks
uv run ruff check && uv run mypy && uv run pytest
```

### Common Issues
- **Tests failing**: Run specific test with `uv run pytest path/to/test.py -v`
- **Design conflicts**: Document in `ai/memory/architecture-decisions.md`
- **Complex implementation**: Break into smaller pieces, write tests first
- **Dependency issues**: Check `docs/contributor/design/technology-decisions.md`

**For complete troubleshooting guide, see `docs/contributor/DEVELOPMENT.md`**

## Project Evolution Guidelines

### Technology Updates
1. **Check rationale** in `docs/contributor/design/technology-decisions.md`
2. **Document motivation** and assess impact
3. **Update in stages** with thorough testing
4. **Update memory files** with new patterns

### Architecture Changes
1. **Update design documents first** before implementing
2. **Document migration strategy** and breaking changes
3. **Implement incrementally** with validation at each phase

**For complete evolution guidelines, see `docs/contributor/design/development-workflow.md`**

## Development Tools Integration

### Essential Tools Setup
```bash
# Install pre-commit hooks
uv run pre-commit install

# Quality checks with auto-fix
uv run ruff check --fix && uv run ruff format
uv run mypy && uv run pytest
```

### Automated Development Workflow
```bash
# Complete quality check and fix cycle (ALL MUST PASS)
uv run ruff check --fix  # Auto-fix issues
uv run ruff format       # Format code
uv run mypy             # Type check - MUST show no errors
uv run pytest          # Run tests - MUST show 100% pass rate

# Verify pre-commit hooks pass (MANDATORY before committing)
uv run pre-commit run --all-files  # ALL hooks MUST pass
```

### 🚨 Commit Requirements (NON-NEGOTIABLE)
Before any commit, verify:
```bash
# These commands MUST return success (exit code 0)
uv run pytest          # 100% test success required
uv run pre-commit run --all-files  # All hooks must pass
```

**If ANY test fails or ANY pre-commit hook fails: FIX BEFORE COMMITTING**

### IDE Configuration
**For complete VSCode settings and extensions, see `docs/contributor/DEVELOPMENT.md`**

Key requirements:
- Ruff for formatting and linting
- MyPy for type checking
- Python language server (Pylance)

### CI/CD Integration
**For complete CI/CD pipeline, see `docs/contributor/design/development-workflow.md`**

All quality gates must pass:
- Code formatting and linting
- Type checking
- Test suite
- Documentation validation

## Quick Reference

### Need Information?
1. **Project understanding**: `ai/memory/project-context.md`
2. **Current priorities**: `ai/memory/current-focus.md`
3. **Architecture details**: `docs/contributor/design/architecture-overview.md`
4. **Development tasks**: `ai/memory/bootstrap-tasks.md`
5. **Coding standards**: `ai/memory/ai-style-guide.md`

### Common Questions
- **"What is this project?"** → `ai/memory/project-context.md`
- **"What should I work on?"** → `ai/memory/current-focus.md`
- **"How does the system work?"** → `docs/contributor/design/architecture-overview.md`
- **"Why this technology choice?"** → `docs/contributor/design/technology-decisions.md`
- **"How do I code this?"** → `ai/memory/ai-style-guide.md` + `ai/memory/patterns.md`

## 🚨 Critical Reminders for AI Assistants

### Code Quality Standards
- **ALWAYS follow `ai/memory/ai-style-guide.md`** - Non-negotiable coding standards
- **Module-only imports**: Never import functions/classes directly (e.g., use `pathlib.Path`, not `from pathlib import Path`)
- **Type hints required**: Use modern Python 3.10+ syntax (`list[str]` not `List[str]`)
- **Test first**: Write comprehensive tests for all new functionality
- **Quality gates**: Run `uv run ruff check`, `uv run mypy`, `uv run pytest` before any commit
- **🚨 MANDATORY**: 100% test pass rate and 100% pre-commit hook success required for ALL commits

### Documentation Maintenance
- **Follow design guidance**: Always reference existing design documents in `docs/contributor/design/` for consistency
- **Update documentation**: When developing new features, update relevant docs (user docs, design docs, CLI reference)
- **Design-driven development**: Consult architecture and design patterns before implementing new features
- **User vs Contributor docs**: Update user docs (`docs/user/`) for end-user features, contributor docs for development changes

### Style Guide Synchronization
- **When `docs/contributor/code-style.md` changes**: IMMEDIATELY update `ai/memory/ai-style-guide.md`
- **Maintain AI optimization**: Keep the condensed guide focused on patterns AI assistants need most
- **Verify completeness**: Ensure critical patterns from the full guide are captured in the AI version

## Authoritative Documentation Sources

**Always reference these authoritative sources for complete information:**

### Project Understanding
- `ai/memory/project-context.md` - High-level project overview
- `docs/contributor/design/project-vision.md` - Complete product vision

### Architecture & Design  
- `docs/contributor/design/architecture-overview.md` - System architecture
- `docs/contributor/design/technology-decisions.md` - Technology choices
- `ai/memory/architecture-decisions.md` - Development decisions (ADR format)

### Development
- `docs/contributor/DEVELOPMENT.md` - Environment setup
- `docs/contributor/code-style.md` - Complete coding standards
- `ai/memory/ai-style-guide.md` - AI-optimized coding guide
- `ai/memory/patterns.md` - Proven development patterns

### Current Work
- `ai/memory/current-focus.md` - Active priorities and session handoffs
- `ai/memory/bootstrap-tasks.md` - Specific development tasks

---

**Ready to build something useful for open source maintainers!** 🚀

*Remember: This tool helps maintainers answer "Cá bhfuil?" (where is?) for their commits across complex git histories.*
