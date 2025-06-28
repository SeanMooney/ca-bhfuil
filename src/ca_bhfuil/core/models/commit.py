"""Commit-related data models."""

import datetime

import pydantic


class CommitInfo(pydantic.BaseModel):
    """Information about a git commit."""

    model_config = pydantic.ConfigDict(
        json_encoders={datetime.datetime: lambda v: v.isoformat()}
    )

    sha: str = pydantic.Field(..., description="Full commit SHA hash")
    short_sha: str = pydantic.Field(
        ..., description="Short commit SHA (first 7 characters)"
    )
    message: str = pydantic.Field(..., description="Commit message")
    author_name: str = pydantic.Field(..., description="Author name")
    author_email: str = pydantic.Field(..., description="Author email")
    author_date: datetime.datetime = pydantic.Field(..., description="Author date")
    committer_name: str = pydantic.Field(..., description="Committer name")
    committer_email: str = pydantic.Field(..., description="Committer email")
    committer_date: datetime.datetime = pydantic.Field(
        ..., description="Committer date"
    )
    parents: list[str] = pydantic.Field(
        default_factory=list, description="Parent commit SHAs"
    )
    branches: list[str] = pydantic.Field(
        default_factory=list, description="Branches containing this commit"
    )
    tags: list[str] = pydantic.Field(
        default_factory=list, description="Tags pointing to this commit"
    )
    files_changed: int | None = pydantic.Field(
        None, description="Number of files changed"
    )
    insertions: int | None = pydantic.Field(None, description="Number of insertions")
    deletions: int | None = pydantic.Field(None, description="Number of deletions")

    def __str__(self) -> str:
        """String representation of commit info."""
        return f"{self.short_sha}: {self.message[:50]}..."
