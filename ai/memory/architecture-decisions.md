# Architecture Decisions

## Core Architecture Decisions

This document tracks key architectural decisions made for Ca-Bhfuil development.

## Decision: SQLModel ORM Adoption
**Date**: 2025-06-29  
**Status**: Adopted  
**Context**: Need to replace direct SQL queries with type-safe ORM for maintainability and AI integration

### Problem
Direct SQL queries in the existing database layer create several issues:
- No compile-time type safety for database operations
- Manual SQL string construction prone to errors
- Difficult to maintain complex relationships
- No built-in validation for data models
- Hard to evolve schema as requirements change
- Limited integration with Pydantic models used elsewhere

### Alternatives Considered
1. **Keep Direct SQL**: Continue with existing `sqlite3` approach
   - Pros: Simple, lightweight, full control
   - Cons: No type safety, manual query construction, maintenance burden
2. **Pure SQLAlchemy**: Use SQLAlchemy Core/ORM without SQLModel
   - Pros: Mature, powerful, flexible
   - Cons: Separate Pydantic models needed, more boilerplate
3. **SQLModel (Selected)**: FastAPI creator's unified Pydantic + SQLAlchemy solution
   - Pros: Type safety, unified models, async support, Pydantic integration
   - Cons: Newer library, some mypy quirks

### Rationale
SQLModel was chosen because it provides:
- **Type Safety**: Full mypy compatibility with proper type hints
- **Unified Models**: Single model definition for database and API/validation
- **Async Support**: Native async/await patterns with aiosqlite
- **Pydantic Integration**: Seamless validation and serialization
- **Future AI Readiness**: Knowledge graph and vector embedding models
- **Repository Pattern**: Clean separation of concerns

### Impact
- **Performance**: Minimal impact, still uses SQLite with better connection management
- **Development**: Significantly improved developer experience with type safety
- **Users**: No user-facing changes, purely internal improvement
- **Future**: Ready for AI features with knowledge graph and vector embeddings

### Implementation Notes
- Repository pattern implemented for clean database abstraction
- Async SQLAlchemy engine with aiosqlite driver
- Type ignores used for SQLModel column methods (like, desc) due to mypy limitations
- JSON columns for flexible metadata storage in knowledge graph models
- Database moved to state directory following XDG standards

### Reversibility
Medium difficulty - would require rewriting database layer but schema remains compatible

### Remaining Work
1. **Test Migration**: Update all tests to use new SQLModel infrastructure
2. **Data Migration**: Create migration script for existing SQLite databases  
3. **Integration**: Update all code that uses database to use new managers
4. **Documentation**: Update contributor docs with new database patterns

### ADR-001: XDG Base Directory Specification Compliance
**Date**: 2025-01-21  
**Status**: Adopted  

**Context**: Need to follow Linux best practices for data storage and respect user preferences.

**Decision**: Implement full XDG Base Directory Specification compliance:
- Configuration: `$XDG_CONFIG_HOME/ca-bhfuil` (default: `~/.config/ca-bhfuil`)
- State: `$XDG_STATE_HOME/ca-bhfuil` (default: `~/.local/state/ca-bhfuil`)  
- Cache: `$XDG_CACHE_HOME/ca-bhfuil` (default: `~/.cache/ca-bhfuil`)

**Consequences**:
- ✅ Standards compliant and user-friendly
- ✅ Proper data separation for backup strategies
- ✅ System integration friendly
- ⚠️ More complex path resolution logic needed

### ADR-002: URL-Based Repository Organization
**Date**: 2025-01-21  
**Status**: Adopted  

**Context**: Need intuitive, collision-free repository organization that scales.

**Decision**: Use URL-based directory structure mirroring git hosting:
```
repos/github.com/torvalds/linux/
repos/git.kernel.org/torvalds/linux/
repo_state/github.com/torvalds/linux/
```

**Consequences**:
- ✅ No slug generation complexity
- ✅ Intuitive navigation
- ✅ Natural multi-source support
- ✅ Collision-free organization
- ⚠️ Requires robust URL parsing

### ADR-003: Separate Authentication Configuration  
**Date**: 2025-01-21  
**Status**: Adopted  

**Context**: Security requirement to keep auth info separate from git-committable configs.

**Decision**:
- Main configs (`repositories.yaml`, `global-settings.yaml`) are git-safe
- Authentication in separate `auth.yaml` file (git-ignored)
- SSH keys preferred over tokens as default
- Environment variable integration for secrets

**Consequences**:
- ✅ Git-safe project configuration sharing
- ✅ Better security practices
- ✅ Flexible authentication options
- ⚠️ Additional configuration complexity

### ADR-004: SQLite Schema Versioning
**Date**: 2025-01-21  
**Status**: Adopted  

**Context**: Need future-proof database schemas with migration support.

**Decision**: All SQLite databases include `schema_info` table with:
- Version tracking
- Migration history
- Ca-Bhfuil version compatibility

**Consequences**:
- ✅ Future-proof for schema changes
- ✅ Safe upgrades and migrations
- ✅ Version compatibility tracking
- ⚠️ Additional database setup complexity

### ADR-005: Lock File Management
**Date**: 2025-01-21  
**Status**: Adopted  

**Context**: Need safe concurrent operations on repository state.

**Decision**: File-based locking system:
- `.locks/` directory in each repository state folder
- Separate locks for sync and analysis operations
- Timeout-based lock acquisition
- Process ID tracking

**Consequences**:
- ✅ Safe concurrent operations
- ✅ Clear operation boundaries
- ✅ Timeout prevents deadlocks
- ⚠️ Cross-platform lock handling needed

### ADR-006: CLI Pattern Standardization
**Date**: 2025-01-21  
**Status**: Adopted  

**Context**: Need consistent, intuitive CLI interface.

**Decision**: Standardize on pattern: `ca-bhfuil <resource> <operation> [--options] [args]`
- Use `--all` flags instead of separate `-all` commands
- Support both names and URLs for repository identification
- Consistent help and error patterns

**Consequences**:
- ✅ Predictable CLI interface
- ✅ Follows common CLI conventions
- ✅ Extensible pattern
- ⚠️ Requires consistent implementation

### ADR-007: pygit2 for Git Operations
**Date**: Earlier (confirmed 2025-01-21)  
**Status**: Adopted  

**Context**: Need high-performance git operations for large repositories.

**Decision**: Use pygit2 (LibGit2 bindings) over GitPython for all git operations.

**Consequences**:
- ✅ 10x+ performance improvement for large repos
- ✅ More efficient memory usage
- ✅ Battle-tested git implementation
- ⚠️ More complex installation (requires libgit2)
- ⚠️ Less Pythonic API

### ADR-008: Local-First Storage Strategy
**Date**: Earlier (confirmed 2025-01-21)  
**Status**: Adopted  

**Context**: Need offline capability and performance.

**Decision**: All storage is local using SQLite and file system:
- No external database dependencies
- Aggressive local caching
- File-based configuration
- Optional remote synchronization

**Consequences**:
- ✅ Offline-first operation
- ✅ Simple deployment
- ✅ No external dependencies
- ✅ Better performance
- ⚠️ Manual backup responsibility

## Implementation Guidelines

### Configuration Management
- Always check XDG environment variables first
- Provide sensible defaults for non-XDG systems
- Validate configuration on load
- Support environment variable overrides

### File Operations
- Set appropriate permissions (700 for sensitive dirs)
- Handle cross-platform path issues
- Implement path length limits for Windows
- Sanitize filesystem-unsafe characters

### Git Operations
- Always use pygit2 for performance
- Implement timeout handling
- Cache results aggressively
- Handle authentication gracefully

### Error Handling
- Provide helpful error messages
- Log appropriately for debugging
- Fail gracefully with cleanup
- Respect user's log level preferences

These decisions form the foundation for Ca-Bhfuil's implementation and should be referenced during development to ensure consistency.
