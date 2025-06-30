# Data Model Architecture Design

> **Strategic approach for data models that balance simplicity with powerful AI capabilities**
>
> **Version**: 1.0 | **Date**: 2025-06-30 | **Status**: Active

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Principles](#design-principles)
3. [Current State Analysis](#current-state-analysis)
4. [Core Components](#core-components)
5. [Evolution Strategy](#evolution-strategy)
6. [Implementation Patterns](#implementation-patterns)
7. [Vector Embeddings & Knowledge Graphs](#vector-embeddings--knowledge-graphs)
8. [Benefits & Trade-offs](#benefits--trade-offs)
9. [Implementation Guidelines](#implementation-guidelines)
10. [Future Considerations](#future-considerations)

## Architecture Overview

Ca-Bhfuil uses a **Manager + Rich Models** architecture that provides clean separation between business logic and database persistence while maintaining low complexity. This approach scales gracefully from basic git operations to sophisticated AI-powered features.

### Core Pattern

```
Business Logic Layer:    Rich Models + Manager Classes
                        ↓ (conversion methods)
Persistence Layer:      Database Models + Repository Pattern
```

**Key Insight**: Instead of complex multi-layer architectures, we use **focused managers** that orchestrate between rich business models and simple database persistence.

## Design Principles

### 1. **Simplicity Over Complexity**
- Minimize architectural concepts (2 core: Models + Managers)
- Avoid deep inheritance hierarchies
- Prefer composition over complex abstractions

### 2. **Clean Separation of Concerns**
- **Business Models**: Contain domain logic and behavior
- **Database Models**: Handle persistence and relationships
- **Managers**: Orchestrate operations and data flow

### 3. **Gradual Evolution**
- Architecture supports incremental enhancement
- Each phase is independently useful
- No breaking changes between evolution phases

### 4. **Future-Proof Design**
- Foundation supports vector embeddings and knowledge graphs
- Scales to agentic RAG workflows
- Maintains simplicity even with AI features

## Current State Analysis

### Business Models (`src/ca_bhfuil/core/models/`)

**Purpose**: Pure Pydantic models for domain logic and API operations

```python
# Current: Basic business model
class CommitInfo(pydantic.BaseModel):
    """Business model with git-specific behavior."""
    sha: str
    message: str
    author_name: str
    # ... git fields

    def __str__(self) -> str:
        return f"{self.short_sha}: {self.message[:50]}..."
```

**Usage**: In-memory operations, CLI responses, business logic

### Database Models (`src/ca_bhfuil/storage/database/models.py`)

**Purpose**: SQLModel models for persistence with database relationships

```python
# Current: Database model with persistence metadata
class Commit(TimestampMixin, table=True):
    """Database model with relationships and constraints."""
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    repository_id: int = sqlmodel.Field(foreign_key="repositories.id")
    sha: str = sqlmodel.Field(index=True)
    # ... database fields

    # Relationships
    repository: Repository = sqlmodel.Relationship(back_populates="commits")
```

**Usage**: Database operations, persistence, relational queries

### Current Overlap Challenge

**Problem**: `CommitInfo` and `Commit` models share ~80% of fields but serve different purposes, leading to:
- Field drift between models
- Manual conversion complexity
- Maintenance overhead

## Core Components

### 1. Enhanced Business Models

**Rich models with behavior and conversion methods:**

```python
class CommitInfo(pydantic.BaseModel):
    """Enhanced business model with behavior."""
    sha: str
    message: str
    author_name: str
    # ... business fields

    # Business Logic Methods
    def matches_pattern(self, pattern: str) -> bool:
        """Domain logic: pattern matching."""
        return pattern.lower() in self.message.lower()

    def calculate_impact_score(self) -> float:
        """Domain logic: assess commit impact."""
        base_score = (self.files_changed or 0) + (self.insertions or 0)
        if any(kw in self.message.lower() for kw in ["fix", "bug", "critical"]):
            base_score *= 1.5
        return min(base_score / 100.0, 1.0)

    # Conversion Methods
    def to_db_create(self, repository_id: int) -> CommitCreate:
        """Convert to database creation model."""
        return CommitCreate(
            repository_id=repository_id,
            sha=self.sha,
            message=self.message,
            author_name=self.author_name,
            # ... map all shared fields
        )

    @classmethod
    def from_db_model(cls, db_commit: Commit) -> "CommitInfo":
        """Create business model from database model."""
        return cls(
            sha=db_commit.sha,
            message=db_commit.message,
            author_name=db_commit.author_name,
            # ... map back all fields
        )
```

### 2. Repository Manager

**Single coordination class for basic operations:**

```python
class RepositoryManager:
    """Manages repository operations with automatic persistence."""

    def __init__(self, repo_path: pathlib.Path):
        self.path = repo_path
        self._git_repo = GitRepository(repo_path)
        self._db_repos = DatabaseRepositories()

    async def load_commits(self, *, from_cache: bool = True) -> list[CommitInfo]:
        """Load commits with intelligent caching."""
        if from_cache:
            # Try database first
            db_commits = await self._db_repos.commits.find_by_path(self.path)
            if db_commits:
                return [CommitInfo.from_db_model(c) for c in db_commits]

        # Fall back to git
        git_commits = self._git_repo.get_commits()

        # Cache for future use
        await self._save_commits_to_db(git_commits)

        return git_commits

    async def search_commits(self, pattern: str) -> list[CommitInfo]:
        """Search commits using business logic."""
        commits = await self.load_commits()
        return [c for c in commits if c.matches_pattern(pattern)]

    async def analyze_repository(self) -> AnalysisResult:
        """Complete repository analysis."""
        commits = await self.load_commits()

        return AnalysisResult(
            commit_count=len(commits),
            average_impact=sum(c.calculate_impact_score() for c in commits) / len(commits),
            high_impact_commits=[c for c in commits if c.calculate_impact_score() > 0.7],
            success=True
        )
```

## Evolution Strategy

The architecture evolves through **focused manager addition**, not architectural complexity.

### Phase 1: Basic Operations (Current)

**Components:**
- `RepositoryManager`: Git + database operations
- Rich `CommitInfo`: Business logic + conversions
- Database models: Persistence layer

**Capabilities:**
- Load commits from git/database
- Search with pattern matching
- Basic repository analysis

### Phase 2: AI Enhancement

**Add AI Manager:**

```python
class AIManager:
    """Handles embeddings and knowledge graph operations."""

    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._embedding_model = embedding_model
        self._db_repos = DatabaseRepositories()

    async def ensure_commit_embeddings(self, commits: list[CommitInfo]) -> None:
        """Generate embeddings for commits without them."""
        for commit in commits:
            if not await self._has_embedding(commit.sha):
                content = commit.get_semantic_content()
                embedding = await self._generate_embedding(content)
                await self._store_embedding(commit.sha, embedding)

    async def find_similar_commits(self, query: str, limit: int = 10) -> list[CommitInfo]:
        """Vector similarity search using sqlite-vec."""
        query_embedding = await self._generate_embedding(query)
        similar_shas = await self._vector_search(query_embedding, limit)
        return await self._load_commits_by_shas(similar_shas)

    async def build_knowledge_graph(self, commits: list[CommitInfo]) -> None:
        """Build knowledge graph from commit relationships."""
        for commit in commits:
            # Create commit node
            await self._create_kg_node("commit", commit.sha, commit.to_kg_properties())

            # Create parent-child relationships
            for parent_sha in commit.parents:
                await self._create_kg_edge(commit.sha, parent_sha, "follows")
```

**Enhanced Business Models:**

```python
class CommitInfo(pydantic.BaseModel):
    # ... existing fields and methods

    # AI-Enhanced Methods
    def get_semantic_content(self) -> str:
        """Get content optimized for embeddings."""
        return f"""
        Commit: {self.message}

        Author: {self.author_name}
        Date: {self.author_date.isoformat()}
        Files Changed: {self.files_changed or 0}
        Impact: {self.calculate_impact_score():.2f}
        """

    def to_kg_properties(self) -> dict[str, typing.Any]:
        """Convert to knowledge graph node properties."""
        return {
            "message": self.message,
            "author": self.author_name,
            "date": self.author_date.isoformat(),
            "files_changed": self.files_changed,
            "impact_score": self.calculate_impact_score(),
            "semantic_hash": hashlib.sha256(self.get_semantic_content().encode()).hexdigest()
        }
```

### Phase 3: Agentic RAG

**Add RAG Manager:**

```python
class RAGManager:
    """Orchestrates agentic workflows using repository data."""

    def __init__(self, repo_path: pathlib.Path):
        self.repo_manager = RepositoryManager(repo_path)
        self.ai_manager = AIManager()

    async def setup_rag_index(self) -> None:
        """Prepare repository for AI-powered queries."""
        commits = await self.repo_manager.load_commits()
        await self.ai_manager.ensure_commit_embeddings(commits)
        await self.ai_manager.build_knowledge_graph(commits)

    async def query_repository(self, question: str) -> RAGResponse:
        """Answer natural language questions about the repository."""
        # 1. Vector search for relevant commits
        similar_commits = await self.ai_manager.find_similar_commits(question)

        # 2. Knowledge graph traversal for context
        related_commits = await self.ai_manager.find_related_commits(similar_commits)

        # 3. Build comprehensive context
        context = self._build_context(similar_commits, related_commits)

        # 4. Generate AI response
        return await self._generate_answer(question, context)

    async def discover_patterns(self) -> PatternAnalysis:
        """Use AI to discover repository development patterns."""
        commits = await self.repo_manager.load_commits()

        # Cluster similar commits using embeddings
        clusters = await self.ai_manager.cluster_commits(commits)

        # Find patterns using knowledge graph analysis
        patterns = await self.ai_manager.analyze_development_patterns(clusters)

        return PatternAnalysis(
            clusters=clusters,
            patterns=patterns,
            insights=self._generate_insights(patterns)
        )
```

## Implementation Patterns

### 1. Conversion Pattern

**Explicit conversion between business and database models:**

```python
# Business → Database
def to_db_create(self, repository_id: int) -> CommitCreate:
    """Convert business model to database creation model."""
    return CommitCreate(
        repository_id=repository_id,
        sha=self.sha,
        # ... explicit field mapping
    )

# Database → Business  
@classmethod
def from_db_model(cls, db_commit: Commit) -> "CommitInfo":
    """Convert database model to business model."""
    return cls(
        sha=db_commit.sha,
        # ... explicit field mapping
    )
```

### 2. Manager Orchestration Pattern

**Managers coordinate between layers:**

```python
class RepositoryManager:
    async def operation(self) -> BusinessResult:
        # 1. Load/generate business data
        business_objects = self._get_business_data()

        # 2. Transform for persistence
        db_objects = [obj.to_db_create() for obj in business_objects]

        # 3. Persist via repository pattern
        await self._db_repos.bulk_create(db_objects)

        # 4. Return business result (not database objects)
        return BusinessResult(data=business_objects)
```

### 3. Progressive Enhancement Pattern

**Each manager adds capabilities without changing others:**

```python
# Basic usage (Phase 1)
repo = RepositoryManager(path)
commits = await repo.search_commits("bug fix")

# Add AI capabilities (Phase 2)
ai = AIManager()
await ai.ensure_commit_embeddings(commits)
similar = await ai.find_similar_commits("memory leak")

# Full agentic capabilities (Phase 3)
rag = RAGManager(path)
await rag.setup_rag_index()
answer = await rag.query_repository("What commits fixed memory issues last month?")
```

## Vector Embeddings & Knowledge Graphs

### Database Foundation (Already Exists)

```python
# Vector embeddings metadata
class EmbeddingRecord(TimestampMixin, table=True):
    source_type: str  # "commit", "file", etc.
    source_id: str    # commit SHA, file path, etc.
    vector_id: str    # reference to sqlite-vec table
    content_hash: str # for change detection
    metadata_: dict[str, Any]  # additional context

# Knowledge graph nodes
class KGNode(TimestampMixin, table=True):
    node_type: str    # "commit", "author", "file", etc.
    node_id: str      # unique identifier
    properties: dict[str, Any]  # flexible node data

# Knowledge graph relationships
class KGEdge(TimestampMixin, table=True):
    source_id: int    # source node
    target_id: int    # target node
    edge_type: str    # "follows", "modifies", "authored_by", etc.
    properties: dict[str, Any]  # relationship metadata
```

### AI Manager Implementation

```python
class AIManager:
    async def _generate_embedding(self, content: str) -> list[float]:
        """Generate vector embedding for content."""
        # Use sentence-transformers, OpenAI, or local model
        pass

    async def _vector_search(self, query_embedding: list[float], limit: int) -> list[str]:
        """Perform vector similarity search using sqlite-vec."""
        query = """
        SELECT er.source_id
        FROM embedding_records er
        JOIN vec_commits vc ON er.vector_id = vc.id
        WHERE er.source_type = 'commit'
        ORDER BY vc.embedding <-> ?
        LIMIT ?
        """
        return await self._db.execute_vector_query(query, query_embedding, limit)

    async def _traverse_kg(self, start_node: str, edge_type: str, direction: str = "outgoing") -> list[str]:
        """Traverse knowledge graph relationships."""
        if direction == "outgoing":
            query = """
            SELECT target.node_id
            FROM kg_nodes source
            JOIN kg_edges e ON source.id = e.source_id  
            JOIN kg_nodes target ON e.target_id = target.id
            WHERE source.node_id = ? AND e.edge_type = ?
            """
        else:  # incoming
            query = """
            SELECT source.node_id
            FROM kg_nodes target
            JOIN kg_edges e ON target.id = e.target_id
            JOIN kg_nodes source ON e.source_id = source.id  
            WHERE target.node_id = ? AND e.edge_type = ?
            """
        return await self._db.execute_query(query, start_node, edge_type)
```

### Knowledge Graph Schema Design

```python
# Node Types
NODE_TYPES = {
    "commit": "Git commit",
    "author": "Code author",
    "file": "Source file",
    "directory": "Directory/module",
    "issue": "Issue/bug reference",
    "branch": "Git branch",
    "tag": "Git tag"
}

# Edge Types  
EDGE_TYPES = {
    "follows": "Commit ancestry (parent → child)",
    "modifies": "Commit modifies file/directory",
    "authored_by": "Commit authored by person",
    "references": "Commit references issue",
    "tagged_as": "Commit tagged with version",
    "branched_from": "Branch relationship",
    "similar_to": "Semantic similarity",
    "fixes": "Commit fixes issue",
    "reverts": "Commit reverts another commit"
}
```

## Benefits & Trade-offs

### ✅ Benefits

**Simplicity & Maintainability:**
- Only 2 core concepts: Models + Managers
- No complex inheritance hierarchies
- Easy to understand and modify

**Clean Separation:**
- Business logic isolated in business models
- Database concerns isolated in database models
- Clear data flow via explicit conversion

**Evolutionary Design:**
- Graceful scaling from basic to AI-powered features
- Each evolution phase independently useful
- No breaking changes between phases

**AI-Ready Foundation:**
- Database models already support embeddings + knowledge graphs
- Business models easily enhanced with AI methods
- Managers orchestrate complex AI workflows

### ⚠️ Trade-offs

**Model Duplication:**
- Business and database models share similar fields
- Requires explicit conversion methods
- Maintenance overhead for field synchronization

**Manager Coordination:**
- Complex operations require multiple manager interaction
- Potential for inconsistent state if not carefully managed
- Testing complexity for multi-manager workflows

**Performance Considerations:**
- Conversion overhead between model types
- Multiple database round-trips for complex operations
- Memory usage for keeping both model types

### Mitigation Strategies

**Field Synchronization:**
- Use shared base models where appropriate
- Automated tests for conversion method completeness
- Clear documentation of field mappings

**Manager Coordination:**
- Transaction boundaries around multi-manager operations
- Clear error handling and rollback strategies
- Comprehensive integration tests

**Performance Optimization:**
- Lazy loading patterns for expensive operations
- Caching strategies for frequently accessed data
- Batch operations where possible

## Implementation Guidelines

### 1. Business Model Enhancement

**Required Methods:**
```python
class BusinessModel(pydantic.BaseModel):
    # Conversion methods (required)
    def to_db_create(self, **kwargs) -> DatabaseCreateModel: ...

    @classmethod  
    def from_db_model(cls, db_model: DatabaseModel) -> "BusinessModel": ...

    # Business logic methods (as needed)
    def domain_specific_behavior(self) -> ResultType: ...
```

**Optional AI Enhancement:**
```python
class BusinessModel(pydantic.BaseModel):
    # AI methods (when AI features are added)
    def get_semantic_content(self) -> str: ...
    def to_kg_properties(self) -> dict[str, Any]: ...
    def calculate_semantic_similarity(self, other: "BusinessModel") -> float: ...
```

### 2. Manager Implementation

**Standard Manager Pattern:**
```python
class DomainManager:
    def __init__(self, dependencies: Dependencies):
        self._dependencies = dependencies

    async def primary_operation(self) -> BusinessResult:
        """Main operation with business logic."""
        # 1. Load/generate business objects
        # 2. Apply business logic  
        # 3. Persist via conversion + repositories
        # 4. Return business result

    async def _private_helper(self) -> InternalType:
        """Private implementation details."""
        pass
```

### 3. Testing Strategy

**Business Model Tests:**
```python
def test_business_logic():
    """Test business behavior in isolation."""
    model = BusinessModel(...)
    assert model.domain_behavior() == expected_result

def test_conversion_roundtrip():
    """Test conversion methods preserve data."""
    business_model = BusinessModel(...)
    db_model = business_model.to_db_create()
    converted_back = BusinessModel.from_db_model(db_model)
    assert business_model == converted_back
```

**Manager Tests:**
```python
async def test_manager_operation(mock_repositories):
    """Test manager orchestration."""
    manager = DomainManager(mock_repositories)
    result = await manager.primary_operation()
    assert result.success
    mock_repositories.verify_expected_calls()
```

## Future Considerations

### Scaling to Larger Repositories

**Challenges:**
- Memory usage for large commit histories
- Vector search performance at scale
- Knowledge graph traversal complexity

**Solutions:**
- Streaming/pagination for large datasets
- Hierarchical embeddings (commit → file → line level)
- Graph database optimization techniques
- Incremental indexing strategies

### Advanced AI Features

**Potential Enhancements:**
- Multi-modal embeddings (code + commit messages + diffs)
- Dynamic knowledge graph construction
- Agentic workflow orchestration
- Real-time semantic analysis

**Architecture Adaptability:**
- Manager pattern scales to specialized AI managers
- Business models can be enhanced with new AI methods
- Database models support flexible metadata storage

### Performance Optimization

**Current Bottlenecks:**
- Model conversion overhead
- Multiple database queries for complex operations
- Vector search scalability

**Optimization Strategies:**
- Batch conversion utilities
- Query optimization and caching
- Async/parallel processing patterns
- Specialized data structures for hot paths

---

## Conclusion

The **Manager + Rich Models** architecture provides an optimal balance between simplicity and capability. It maintains clean separation of concerns while supporting graceful evolution from basic git operations to sophisticated AI-powered agentic workflows.

**Key Success Factors:**
1. **Start Simple**: Basic repository operations with clean model separation
2. **Evolve Gradually**: Add focused managers for new capabilities  
3. **Maintain Boundaries**: Business logic in models, orchestration in managers
4. **Test Thoroughly**: Each layer and conversion pattern
5. **Document Decisions**: Clear rationale for architectural choices

This approach ensures ca-bhfuil can grow from a useful git repository analysis tool into a powerful agentic platform while maintaining code quality and developer productivity.

---

**Document Metadata:**
- **Author**: AI Assistant (Claude)
- **Review Status**: Draft
- **Next Review**: After Phase 1 implementation
- **Related Documents**:
  - `technology-decisions.md`: Technology stack rationale
  - `data-storage-design.md`: Database schema details
  - `architecture-overview.md`: Overall system design
