# Custom Claude Session Commands

> **Custom commands for managing AI development sessions on Ca-Bhfuil**
>
> **Last Updated**: 2025-06-27

## Available Commands

### Group 1: Essential Session Management

#### `/project:start-session [type]`
**Purpose**: Initialize a new development session with proper context loading

**Usage**: `/project:start-session [feature|bugfix|refactor|docs|maintenance]`

**Implementation**:
```
1. Read all ai/memory/ files for current context
2. Check git status and recent commits  
3. Display current project status and priorities
4. Create session entry in current-focus.md
5. Show recommended next steps based on session type
```

#### `/project:end-session`
**Purpose**: Properly close a development session with handoff documentation

**Implementation**:
```
1. Update current-focus.md with session handoff
2. Check for uncommitted changes and prompt to commit
3. Update memory files with new patterns/decisions discovered
4. Create session summary if significant work was accomplished
5. Prepare handoff information for next AI assistant
```

#### `/project:session-status`
**Purpose**: Quick overview of current session and project status

**Implementation**:
```
1. Display current session info from current-focus.md
2. Show git status and recent commits (last 5)
3. List current tasks from bootstrap-tasks.md
4. Show any blockers or immediate next steps
5. Display project phase and completion status
```

### Group 2: High Value Commands

#### `/project:quality-check`
**Purpose**: Run comprehensive quality gates before committing

**Implementation**:
```
1. Run code formatting: uv run ruff check && uv run ruff format
2. Run type checking: uv run mypy
3. Run test suite: uv run pytest
4. Check for documentation updates needed
5. Validate memory file updates are complete
6. Report any issues found with suggestions
```

#### `/project:show-status`
**Purpose**: Display comprehensive project status from memory files

**Implementation**:
```
1. Read and display ai/memory/project-status.md
2. Show current implementation phase and progress
3. List completed phases and next priorities
4. Display any blockers or dependencies
5. Show links to relevant documentation
```

#### `/project:update-memory`
**Purpose**: Update memory files with new insights and decisions

**Implementation**:
```
1. Prompt for what type of updates to make
2. Update relevant memory files based on current work
3. Sync ai-style-guide.md with code-style.md if needed
4. Add new patterns to patterns.md if discovered
5. Update architecture-decisions.md with new ADRs if applicable
6. Update current-focus.md with progress
```

## Command Implementation Status

- [ ] `/project:start-session` - Ready to implement
- [ ] `/project:end-session` - Ready to implement  
- [ ] `/project:session-status` - Ready to implement
- [ ] `/project:quality-check` - Ready to implement
- [ ] `/project:show-status` - Ready to implement
- [ ] `/project:update-memory` - Ready to implement

## Implementation Notes

### File Reading Pattern
Commands that read memory files should use this pattern:
1. Check if file exists
2. Read content and parse relevant sections
3. Display formatted output with clear structure
4. Handle any file read errors gracefully

### Git Integration
Commands that interact with git should:
1. Use proper error handling for git operations
2. Display user-friendly output
3. Respect current working directory
4. Handle repository detection gracefully

### Memory File Updates
Commands that update memory files should:
1. Preserve existing structure and formatting
2. Add timestamps to new entries
3. Maintain consistency with existing patterns
4. Validate changes before writing

### Error Handling
All commands should:
1. Provide clear error messages
2. Suggest corrective actions when possible
3. Gracefully handle missing files or git repository
4. Maintain session state even if commands fail

---

**Usage**: These commands are designed to be invoked as custom prompts in Claude Code to streamline AI development workflow on the Ca-Bhfuil project.

they will be created following https://docs.anthropic.com/en/docs/claude-code/slash-commands#syntax
in .claude/commands/ following the project command structure.
