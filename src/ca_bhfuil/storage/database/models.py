"""SQLModel database models for ca-bhfuil."""

import datetime
import typing

import sqlalchemy
import sqlmodel


class TimestampMixin(sqlmodel.SQLModel):
    """Mixin class for adding timestamp fields to models."""

    created_at: datetime.datetime = sqlmodel.Field(
        default_factory=datetime.datetime.utcnow,
        description="Creation timestamp",
        sa_column_kwargs={"server_default": sqlmodel.text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime.datetime = sqlmodel.Field(
        default_factory=datetime.datetime.utcnow,
        description="Last update timestamp",
        sa_column_kwargs={
            "server_default": sqlmodel.text("CURRENT_TIMESTAMP"),
            "onupdate": sqlmodel.text("CURRENT_TIMESTAMP"),
        },
    )


class Repository(TimestampMixin, table=True):
    """Repository model for tracking git repositories."""

    __tablename__ = "repositories"

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    path: str = sqlmodel.Field(unique=True, index=True, description="Repository path")
    name: str = sqlmodel.Field(description="Repository name")
    last_analyzed: datetime.datetime | None = sqlmodel.Field(
        default=None, description="Last analysis timestamp"
    )
    commit_count: int = sqlmodel.Field(default=0, description="Number of commits")
    branch_count: int = sqlmodel.Field(default=0, description="Number of branches")

    # Relationships
    commits: list["Commit"] = sqlmodel.Relationship(back_populates="repository")
    branches: list["Branch"] = sqlmodel.Relationship(back_populates="repository")


class Commit(TimestampMixin, table=True):
    """Commit model for storing git commit information."""

    __tablename__ = "commits"

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    repository_id: int = sqlmodel.Field(
        foreign_key="repositories.id", description="Repository ID"
    )
    sha: str = sqlmodel.Field(index=True, description="Full commit SHA hash")
    short_sha: str = sqlmodel.Field(index=True, description="Short commit SHA")
    message: str = sqlmodel.Field(description="Commit message")
    author_name: str = sqlmodel.Field(description="Author name")
    author_email: str = sqlmodel.Field(description="Author email")
    author_date: datetime.datetime = sqlmodel.Field(
        index=True, description="Author date"
    )
    committer_name: str = sqlmodel.Field(description="Committer name")
    committer_email: str = sqlmodel.Field(description="Committer email")
    committer_date: datetime.datetime = sqlmodel.Field(description="Committer date")
    files_changed: int | None = sqlmodel.Field(
        default=None, description="Number of files changed"
    )
    insertions: int | None = sqlmodel.Field(
        default=None, description="Number of insertions"
    )
    deletions: int | None = sqlmodel.Field(
        default=None, description="Number of deletions"
    )

    # Relationships
    repository: Repository = sqlmodel.Relationship(back_populates="commits")
    commit_branches: list["CommitBranch"] = sqlmodel.Relationship(
        back_populates="commit"
    )

    # Unique constraint on repository_id + sha
    __table_args__ = (sqlmodel.UniqueConstraint("repository_id", "sha"),)


class Branch(TimestampMixin, table=True):
    """Branch model for tracking git branches."""

    __tablename__ = "branches"

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    repository_id: int = sqlmodel.Field(
        foreign_key="repositories.id", description="Repository ID"
    )
    name: str = sqlmodel.Field(index=True, description="Branch name")
    target_sha: str | None = sqlmodel.Field(
        default=None, description="Target commit SHA"
    )
    is_remote: bool = sqlmodel.Field(default=False, description="Is remote branch")

    # Relationships
    repository: Repository = sqlmodel.Relationship(back_populates="branches")
    commit_branches: list["CommitBranch"] = sqlmodel.Relationship(
        back_populates="branch"
    )

    # Unique constraint on repository_id + name
    __table_args__ = (sqlmodel.UniqueConstraint("repository_id", "name"),)


class CommitBranch(sqlmodel.SQLModel, table=True):
    """Junction table for commit-branch relationships."""

    __tablename__ = "commit_branches"

    commit_id: int = sqlmodel.Field(
        foreign_key="commits.id", primary_key=True, description="Commit ID"
    )
    branch_id: int = sqlmodel.Field(
        foreign_key="branches.id", primary_key=True, description="Branch ID"
    )

    # Relationships
    commit: Commit = sqlmodel.Relationship(back_populates="commit_branches")
    branch: Branch = sqlmodel.Relationship(back_populates="commit_branches")


# Vector embedding and knowledge graph models for future AI features
class EmbeddingRecord(TimestampMixin, table=True):
    """Model for storing vector embedding metadata."""

    __tablename__ = "embedding_records"

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    source_type: str = sqlmodel.Field(description="Type of source (commit, file, etc.)")
    source_id: str = sqlmodel.Field(description="ID of the source object")
    vector_id: str = sqlmodel.Field(
        unique=True, description="Reference to vector in sqlite-vec table"
    )
    content_hash: str = sqlmodel.Field(
        description="Hash of the content for change detection"
    )
    metadata_: dict[str, typing.Any] = sqlmodel.Field(
        default_factory=dict,
        description="Additional metadata",
        sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON),
    )


class KGNode(TimestampMixin, table=True):
    """Knowledge graph node model."""

    __tablename__ = "kg_nodes"

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    node_type: str = sqlmodel.Field(index=True, description="Type of node")
    node_id: str = sqlmodel.Field(description="Unique identifier for the node")
    properties: dict[str, typing.Any] = sqlmodel.Field(
        default_factory=dict,
        description="Node properties",
        sa_column=sqlalchemy.Column(sqlalchemy.JSON),
    )

    # Relationships
    outgoing_edges: list["KGEdge"] = sqlmodel.Relationship(
        back_populates="source_node",
        sa_relationship_kwargs={"foreign_keys": "KGEdge.source_id"},
    )
    incoming_edges: list["KGEdge"] = sqlmodel.Relationship(
        back_populates="target_node",
        sa_relationship_kwargs={"foreign_keys": "KGEdge.target_id"},
    )

    # Unique constraint on node_type + node_id
    __table_args__ = (sqlmodel.UniqueConstraint("node_type", "node_id"),)


class KGEdge(TimestampMixin, table=True):
    """Knowledge graph edge model."""

    __tablename__ = "kg_edges"

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    source_id: int = sqlmodel.Field(
        foreign_key="kg_nodes.id", description="Source node ID"
    )
    target_id: int = sqlmodel.Field(
        foreign_key="kg_nodes.id", description="Target node ID"
    )
    edge_type: str = sqlmodel.Field(index=True, description="Type of edge")
    properties: dict[str, typing.Any] = sqlmodel.Field(
        default_factory=dict,
        description="Edge properties",
        sa_column=sqlalchemy.Column(sqlalchemy.JSON),
    )

    # Relationships
    source_node: KGNode = sqlmodel.Relationship(
        back_populates="outgoing_edges",
        sa_relationship_kwargs={"foreign_keys": "KGEdge.source_id"},
    )
    target_node: KGNode = sqlmodel.Relationship(
        back_populates="incoming_edges",
        sa_relationship_kwargs={"foreign_keys": "KGEdge.target_id"},
    )


# Pydantic models for API responses (without table=True)
class RepositoryRead(sqlmodel.SQLModel):
    """Repository read model for API responses."""

    id: int
    path: str
    name: str
    last_analyzed: datetime.datetime | None
    commit_count: int
    branch_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CommitRead(sqlmodel.SQLModel):
    """Commit read model for API responses."""

    id: int
    repository_id: int
    sha: str
    short_sha: str
    message: str
    author_name: str
    author_email: str
    author_date: datetime.datetime
    committer_name: str
    committer_email: str
    committer_date: datetime.datetime
    files_changed: int | None
    insertions: int | None
    deletions: int | None
    created_at: datetime.datetime


class BranchRead(sqlmodel.SQLModel):
    """Branch read model for API responses."""

    id: int
    repository_id: int
    name: str
    target_sha: str | None
    is_remote: bool
    created_at: datetime.datetime


# Create and update models
class RepositoryCreate(sqlmodel.SQLModel):
    """Repository creation model."""

    path: str
    name: str


class RepositoryUpdate(sqlmodel.SQLModel):
    """Repository update model."""

    last_analyzed: datetime.datetime | None = None
    commit_count: int | None = None
    branch_count: int | None = None


class CommitCreate(sqlmodel.SQLModel):
    """Commit creation model."""

    repository_id: int
    sha: str
    short_sha: str
    message: str
    author_name: str
    author_email: str
    author_date: datetime.datetime
    committer_name: str
    committer_email: str
    committer_date: datetime.datetime
    files_changed: int | None = None
    insertions: int | None = None
    deletions: int | None = None


class BranchCreate(sqlmodel.SQLModel):
    """Branch creation model."""

    repository_id: int
    name: str
    target_sha: str | None = None
    is_remote: bool = False
