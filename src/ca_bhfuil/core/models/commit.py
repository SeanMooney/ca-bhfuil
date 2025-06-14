"""Commit-related data models."""

from datetime import datetime

from pydantic import BaseModel, Field


class CommitInfo(BaseModel):
    """Information about a git commit."""

    sha: str = Field(..., description="Full commit SHA hash")
    short_sha: str = Field(..., description="Short commit SHA (first 7 characters)")
    message: str = Field(..., description="Commit message")
    author_name: str = Field(..., description="Author name")
    author_email: str = Field(..., description="Author email")
    author_date: datetime = Field(..., description="Author date")
    committer_name: str = Field(..., description="Committer name")
    committer_email: str = Field(..., description="Committer email")
    committer_date: datetime = Field(..., description="Committer date")
    parents: list[str] = Field(default_factory=list, description="Parent commit SHAs")
    branches: list[str] = Field(default_factory=list, description="Branches containing this commit")
    tags: list[str] = Field(default_factory=list, description="Tags pointing to this commit")
    files_changed: int | None = Field(None, description="Number of files changed")
    insertions: int | None = Field(None, description="Number of insertions")
    deletions: int | None = Field(None, description="Number of deletions")

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def __str__(self) -> str:
        """String representation of commit info."""
        return f"{self.short_sha}: {self.message[:50]}..."
