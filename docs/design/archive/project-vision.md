### Single Developer Maintenance
- **Risk**: Abandoned project if life changes
- **Mitigation**: Clear architecture, good documentation, encourage contributors
- **Risk**: File-based storage becoming unwieldy at scale
- **Mitigation**: Intelligent partitioning, automatic cleanup, optional cloud storage for large datasets### AI & Privacy Philosophy### AI Integration Complexity
- **Risk**: Over-reliance on AI making tool unreliable
- **Mitigation**: AI as enhancement layer, core functionality works without LLMs
- **Risk**: Small local models producing inconsistent results
- **Mitigation**: Structured output schemas, task-specific prompts, graceful fallback to non-AI analysis# Cá Bhfuil - Technical Vision & Roadmap

## Project Identity

**Name**: Cá Bhfuil *(pronounced "caw will")*  
**Meaning**: Irish for "where is" - capturing the tool's core purpose  
**License**: MIT License  
**Project Type**: Hobby project for open source maintainers  
**Development Model**: Single developer + AI assistance

## Technical Vision

**Cá Bhfuil is a pragmatic git repository analysis tool that helps open source maintainers track patches, fixes, and features across their stable branches.**

Built by a developer, for developers who maintain complex git repositories with multiple stable branches and need to quickly understand where changes have landed and what still needs backporting.

## Core Problem Statement

### The Open Source Maintainer Pain

Open source project maintainers face these daily challenges:

- **Backport Management**: "Did CVE-2024-1234 get backported to all supported stable branches?"
- **Fix Tracking**: "Where is the fix for this memory leak across our release branches?"
- **Release Planning**: "What fixes are in main but missing from stable/v2.1?"
- **Change Archaeology**: "When was this feature added and is it safe to backport?"
- **Compliance Auditing**: "Show me all security fixes that need backporting"

### Why Git CLI Isn't Enough

The git CLI is powerful but requires complex command chains and deep knowledge:
```bash
# To find where a commit exists across branches
git branch --contains <sha>
git tag --contains <sha>
git log --grep="CVE-2024-1234" --all --oneline
git cherry -v stable/v2.1 main | grep <sha>
```

This becomes unwieldy when tracking multiple changes across many branches, especially when dealing with:
- Cherry-picked commits with different SHAs
- Gerrit Change-IDs that span multiple commits
- Issue tracker references scattered across commit messages
- Understanding what changes are still pending backport

## Solution Architecture

### Core Capabilities

#### 1. **Universal Change Tracking** 🔍
Input any reference and find all related commits:
```bash
ca-bhfuil "CVE-2024-1234"           # Find security fixes
ca-bhfuil I1a2b3c4d5e6f7g8h9i0j     # Gerrit Change-ID
ca-bhfuil abc123def                 # Git SHA (full or partial)
ca-bhfuil "LP#1234567"              # Launchpad bug
ca-bhfuil "memory leak in auth"     # Natural language search
```

#### 2. **Branch Distribution Analysis** 🌳
Understand where changes exist across your branching strategy:
- Detect all branches containing specific commits
- Identify cherry-picks and backports (same Change-ID, different SHA)
- Map commits to release tags and stable branches
- Show what's missing from each stable branch

#### 3. **Backport Status Tracking** 📋
Critical for stable branch maintenance:
- Compare main branch against stable branches
- Identify commits that need backporting
- Detect failed cherry-picks and conflicts
- Track which fixes made it to which releases

#### 4. **AI-Assisted Understanding** 🧠
Leverage AI to make sense of complex change histories:
- Summarize what commits actually changed
- Classify changes (bugfix, feature, security, etc.)
- Identify related commits (fixes, reverts, follow-ups)
- Extract issue tracker references and context

### Technical Implementation

#### **Performance First Design**
Built for large repositories with local-first storage and offline capability:
- **pygit2**: LibGit2 bindings for 10x+ performance over GitPython
- **SQLite-based Persistence**: All caching and data storage using file-based SQLite
- **Offline-First**: Complete functionality without network dependencies
- **diskcache**: SQLite-backed caching with automatic eviction and persistence
- **File-based RAG**: Local vector storage for AI-enhanced search without external databases

#### **AI Integration Strategy**
Local-first AI approach designed for privacy and independence:
- **Primary**: Ollama/vLLM/LMStudio for local model hosting
- **OpenAI-Compatible Interface**: Unified API for all providers (local and remote)
- **Provider-Agnostic**: Support any OpenAI-compatible endpoint
- **Small Model Optimization**: Designed to work with 7B-13B parameter models
- **Privacy First**: Local providers keep repository analysis private
- **Remote Fallback**: OpenRouter integration for enhanced analysis (optional)
- **Structured Output**: Pydantic models ensure reliable responses from all providers
- **Graceful Degradation**: Core functionality works without AI entirely

#### **Issue Tracker Integration**
Support for common open source trackers:
- **Primary**: GitHub Issues, Launchpad, JIRA
- **Secondary**: Gerrit (Change-ID parsing), Bugzilla
- **Pattern Matching**: Regex-based extraction from commit messages
- **Lazy Resolution**: Show links immediately, fetch content on demand

## User Experience Design

### Target User: Open Source Maintainer

**Primary Workflow**: Stable branch maintenance and release management
- Maintain multiple stable branches (e.g., stable/v2.1, stable/v2.0)
- Track security fixes and critical bugs across branches
- Prepare release notes and understand change impact
- Coordinate with contributors on backport requests

### Interaction Patterns

#### **Quick Status Checks**
```bash
# What's the status of this CVE across all branches?
ca-bhfuil "CVE-2024-1234"

# What commits are in main but not in stable/v2.1?
ca-bhfuil --missing-from stable/v2.1

# Where did this commit land?
ca-bhfuil abc123def --distribution
```

#### **Release Preparation**
```bash
# What changed between these tags?
ca-bhfuil --range v2.1.0..v2.1.1 --categorize

# Show all security fixes since last release
ca-bhfuil --security --since v2.1.0

# Generate backport candidate list
ca-bhfuil --backport-candidates stable/v2.1
```

#### **Investigation Mode**
```bash
# Interactive exploration for complex tracking
ca-bhfuil --interactive
> search: authentication memory leak
> analyze: impact and related changes
> backport: check stable branch status
> export: generate report for security team
```

### Output Design Philosophy

**Information Density**: Rich, scannable output that shows relationships clearly
```
🔍 CVE-2024-1234: Authentication memory leak fix

┌─ abc123d - Fix auth validation memory leak (2024-01-15)
│  📍 Branches: main, stable/v2.1, stable/v2.0
│  🏷️  Tags: v2.1.1, v2.0.5
│  🔗 Issues: CVE-2024-1234, LP#1234567
│  ✅ Backported to all stable branches
│  
├─ def456a - Follow-up: Add regression test (2024-01-16)
│  📍 Branches: main, stable/v2.1
│  ❌ Missing from: stable/v2.0
│  
└─ Related Changes:
   📝 ghi789b - Documentation update (main only)
   🧪 jkl012c - Additional test coverage (main only)

⚠️  Recommendation: Consider backporting def456a to stable/v2.0
```

## Roadmap & Implementation Strategy

### Phase 1: Core Functionality (MVP)
**Timeline**: 2-3 months of hobby development

**Essential Features**:
- Basic commit search by SHA, Change-ID, and issue references
- Branch distribution analysis (where commits exist)
- Simple text output with branch/tag information
- Basic caching for performance on large repos

**Technical Deliverables**:
- Basic commit search by SHA, Change-ID, and issue references
- Branch distribution analysis (where commits exist)
- SQLite-based caching and persistence
- File-based storage (no external databases)
- Basic text output with branch/tag information
- Offline-capable core functionality

### Phase 2: Intelligence Layer
**Timeline**: 3-6 months additional development

**Enhanced Features**:
- AI-powered commit summarization and classification
- Backport status analysis and recommendations
- Rich terminal output with visual hierarchy
- Issue tracker API integration (lazy loading)

**Technical Deliverables**:
- PydanticAI integration with OpenAI-compatible providers
- Provider-agnostic embedding generation (Ollama, vLLM, LMStudio, OpenRouter)
- Local RAG implementation with SQLite vector storage
- Small model optimization (structured prompts for 7B-13B models)
- httpx-based issue tracker clients with SQLite caching
- Rich terminal formatting
- Interactive mode with prompt-toolkit
- Unified configuration for multiple AI providers

### Phase 3: Advanced Analysis
**Timeline**: 6+ months (ongoing hobby development)

**Advanced Features**:
- Predictive backport analysis
- Automated release note generation
- Security audit reporting
- Integration with CI/CD workflows

**Technical Deliverables**:
- Advanced RAG-powered repository search
- Automated release note generation
- Security audit reporting with local compliance tracking
- Integration with CI/CD workflows via MCP server
- SQLite-based analytics and trend analysis
- Advanced embedding models for semantic code search

### Development Philosophy

#### **Local-First Everything**
All aspects of the tool prioritize local control and offline capability:
- **Storage**: SQLite files instead of external databases
- **AI**: Local models instead of cloud APIs (with optional fallback)
- **Cache**: File-based persistence instead of in-memory solutions
- **Configuration**: Local files instead of cloud-based settings
- **Dependencies**: Minimal external services, maximum self-containment

#### **Incremental Value**
Each phase delivers immediate value to maintainers:
- Phase 1: Replaces complex git command chains
- Phase 2: Adds intelligence and better UX
- Phase 3: Enables advanced workflows

#### **Single Developer Constraints**
Acknowledging realistic scope and timeline:
- **Focus**: Solve real problems rather than build comprehensive features
- **Quality**: Strong testing and documentation for maintainable codebase
- **Pragmatism**: Use AI assistance for complex features rather than building everything manually
- **Community**: Open source development to attract contributors over time

#### **Sustainability Strategy**
Built for long-term hobby maintenance:
- **Minimal Dependencies**: Only 11 core dependencies to reduce maintenance burden
- **Clear Architecture**: Well-documented code for future contributors
- **Automated Quality**: Pre-commit hooks and CI for consistent code quality
- **Modular Design**: Feature additions don't require core rewrites

## Success Metrics

### Technical Success
- **Performance**: Sub-second response for cached queries on Linux kernel-sized repos
- **Accuracy**: 95%+ success rate in finding commits from various identifiers
- **Reliability**: Handles edge cases in git history (merges, rebases, etc.)
- **Usability**: Reduces multi-step git workflows to single commands

### Community Adoption
- **Real Usage**: 5+ open source projects using it for stable branch management
- **Contributions**: Community contributions to issue tracker plugins
- **Documentation**: Other maintainers can understand and extend the tool
- **Feedback Loop**: Active issues and feature requests from real users

### Personal Development Goals
- **AI Integration**: Practical experience with modern AI tooling (PydanticAI, LLMs)
- **Performance Engineering**: Optimizing Python for large-scale git analysis
- **Open Source Impact**: Creating tools that help the broader community
- **Technical Writing**: Clear documentation and architectural decisions

## Technical Risks & Mitigations

### Repository Scale Challenges
- **Risk**: Performance degradation on massive repositories
- **Mitigation**: Aggressive caching, pygit2 performance, incremental analysis

### Local-First Data Architecture

#### **File-Based Storage Philosophy**
Cá Bhfuil embraces simplicity and independence through file-based storage:

**SQLite as the Primary Backend**
- **Repository Analysis Cache**: Commit metadata, branch relationships, and analysis results
- **Issue Tracker Cache**: API responses and link resolutions stored locally
- **AI Context Storage**: RAG embeddings and analysis history in SQLite with extensions
- **Configuration Management**: User preferences and tool configuration

**No External Dependencies**
- **Zero Database Administration**: No PostgreSQL, MySQL, or Redis required
- **Portable Data**: Entire cache and configuration travels with the repository
- **Version Control Friendly**: Cache databases can be excluded from git with .gitignore
- **Backup Simplicity**: Copy files to backup entire application state

**Offline-First Design**
- **Complete Functionality**: Full repository analysis without network access
- **Cached AI Models**: Local Ollama/vLLM models work offline
- **Persistent Context**: RAG embeddings stored locally for enhanced search
- **Graceful Degradation**: Issue tracker links shown even when APIs unavailable

#### **RAG Storage Strategy**
Local Retrieval Augmented Generation without external vector databases:

**SQLite Vector Extensions**
- **sqlite-vec**: Vector similarity search directly in SQLite
- **Embedding Storage**: Commit message and change embeddings stored locally
- **Efficient Retrieval**: Fast semantic search through repository history
- **Incremental Updates**: Only embed new commits, reuse existing embeddings

**Local Embedding Models**
- **Provider-Hosted Embeddings**: Use embedding models from configured LLM provider (Ollama, vLLM, LMStudio, OpenRouter)
- **OpenAI-Compatible API**: Unified interface for embeddings regardless of provider
- **Repository-Specific**: Build embeddings corpus from actual commit history
- **Privacy Preserving**: Embeddings generated by local providers maintain privacy
- **Network Optional**: Local providers work offline, remote providers require network

#### **Cache Architecture**
Intelligent local caching for performance and offline capability:

**Hierarchical Storage**
```
~/.cache/ca-bhfuil/
├── repos/
│   ├── {repo-hash}/
│   │   ├── analysis.db          # SQLite: commit analysis, branch data
│   │   ├── embeddings.db        # SQLite: RAG vectors from provider APIs
│   │   ├── trackers.db          # SQLite: cached issue tracker data
│   │   └── config.db            # SQLite: repo-specific configuration
│   └── global/
│       ├── providers.yaml       # AI provider configurations
│       └── templates.db         # SQLite: reusable analysis templates
```

**Smart Cache Management**
- **Automatic Eviction**: LRU eviction with configurable size limits
- **Partial Updates**: Only refresh changed branches/commits
- **Cross-Repository Sharing**: Common patterns shared across repos
- **Configurable TTLs**: Different expiration for analysis vs. tracker data

#### **Local-First AI Design**
Cá Bhfuil is built with privacy and local control as primary concerns:

**Primary Mode: Provider-Hosted Models**
- **Ollama Integration**: Primary backend for running LLM and embedding models locally
- **vLLM Support**: High-performance inference server for local network deployment
- **LMStudio Compatibility**: Desktop AI model hosting with OpenAI-compatible API
- **OpenRouter Support**: Remote hosted models with OpenAI-compatible interface
- **Unified Interface**: Single OpenAI-compatible client for all providers

**Structured Prompting for Small Models**
- **Constrained Output**: Pydantic schemas ensure reliable responses from smaller models
- **Context Optimization**: Efficient prompts designed for limited context windows
- **Task Specialization**: Separate small models for different analysis tasks rather than one large model

**Optional Cloud Enhancement**
- **OpenRouter Integration**: Optional fallback for complex analysis requiring larger models
- **Explicit Opt-in**: Cloud usage requires explicit configuration and user consent
- **Selective Usage**: Only non-sensitive summarization tasks, never raw repository content

**Privacy Guarantees**
- **Provider Choice**: User controls whether to use local or remote providers
- **No Model Execution**: Cá Bhfuil doesn't run models directly, only calls APIs
- **Metadata Only**: AI analysis works with commit messages and metadata, not source code
- **Configurable Boundaries**: Clear controls over what data is sent to which provider endpoint

### Issue Tracker API Limitations
- **Risk**: Rate limiting and authentication complexity
- **Mitigation**: Lazy loading, aggressive caching, graceful degradation

### Operational Complexity
- **Risk**: Complex setup and configuration requirements
- **Mitigation**: File-based storage, zero external dependencies, automatic cache management
- **Risk**: Performance degradation with large cache files
- **Mitigation**: SQLite optimization, automatic cleanup, configurable retention policies

---

**Cá Bhfuil: Because tracking changes across stable branches shouldn't require a computer science degree.**

*A pragmatic tool built by a maintainer, for maintainers who just want to know where their fixes landed.*
