"""Commit-related data models."""

import datetime
import typing

import pydantic


# Import for type hints in conversion methods
if typing.TYPE_CHECKING:
    from ca_bhfuil.storage.database import models as db_models


class CommitInfo(pydantic.BaseModel):
    """Information about a git commit."""

    model_config = pydantic.ConfigDict()

    sha: str = pydantic.Field(..., description="Full commit SHA hash")
    short_sha: str = pydantic.Field(
        ..., description="Short commit SHA (first 7 characters)"
    )
    message: str = pydantic.Field(..., description="Commit message")
    author_name: str = pydantic.Field(..., description="Author name")
    author_email: str = pydantic.Field(..., description="Author email")
    author_date: datetime.datetime = pydantic.Field(
        ..., description="Author date", json_schema_extra={"format": "date-time"}
    )
    committer_name: str = pydantic.Field(..., description="Committer name")
    committer_email: str = pydantic.Field(..., description="Committer email")
    committer_date: datetime.datetime = pydantic.Field(
        ..., description="Committer date", json_schema_extra={"format": "date-time"}
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

    # Conversion Methods
    def to_db_create(self, repository_id: int) -> "db_models.CommitCreate":
        """Convert business model to database creation model.

        Args:
            repository_id: ID of the repository this commit belongs to

        Returns:
            CommitCreate model ready for database insertion
        """
        # Lazy import to avoid circular dependencies
        from ca_bhfuil.storage.database import models as db_models  # noqa: PLC0415

        return db_models.CommitCreate(
            repository_id=repository_id,
            sha=self.sha,
            short_sha=self.short_sha,
            message=self.message,
            author_name=self.author_name,
            author_email=self.author_email,
            author_date=self.author_date,
            committer_name=self.committer_name,
            committer_email=self.committer_email,
            committer_date=self.committer_date,
            files_changed=self.files_changed,
            insertions=self.insertions,
            deletions=self.deletions,
        )

    @classmethod
    def from_db_model(cls, db_commit: "db_models.Commit") -> "CommitInfo":
        """Create business model from database model.

        Args:
            db_commit: Database commit model

        Returns:
            CommitInfo business model

        Note:
            branches and tags fields will be empty lists since they're not stored
            directly in the Commit table but derived from relationships.
            parents field will also be empty for the same reason.
        """
        return cls(
            sha=db_commit.sha,
            short_sha=db_commit.short_sha,
            message=db_commit.message,
            author_name=db_commit.author_name,
            author_email=db_commit.author_email,
            author_date=db_commit.author_date,
            committer_name=db_commit.committer_name,
            committer_email=db_commit.committer_email,
            committer_date=db_commit.committer_date,
            files_changed=db_commit.files_changed,
            insertions=db_commit.insertions,
            deletions=db_commit.deletions,
            # Note: parents, branches, tags are not stored directly in Commit table
            # These would need to be populated separately through relationships
            parents=[],
            branches=[],
            tags=[],
        )

    # Business Logic Methods
    def matches_pattern(self, pattern: str) -> bool:
        """Check if this commit matches a search pattern.

        Args:
            pattern: Search pattern to match against

        Returns:
            True if the commit matches the pattern

        Note:
            Searches in commit SHA, short SHA, commit message, author name, and author email.
            Case-insensitive matching.
        """
        pattern_lower = pattern.lower()
        return (
            pattern_lower in self.sha.lower()
            or pattern_lower in self.short_sha.lower()
            or pattern_lower in self.message.lower()
            or pattern_lower in self.author_name.lower()
            or pattern_lower in self.author_email.lower()
        )

    def calculate_impact_score(self) -> float:
        """Calculate a normalized impact score for this commit.

        Returns:
            Float between 0.0 and 1.0 representing commit impact

        Note:
            Based on files changed, insertions, and commit message keywords.
            Returns 0.0 if change statistics are not available.
        """
        if self.files_changed is None and self.insertions is None:
            return 0.0

        # Base score from change metrics
        base_score = (self.files_changed or 0) + (self.insertions or 0)

        # Apply multipliers for important keywords
        message_lower = self.message.lower()
        multiplier = 1.0

        # Critical/urgent changes
        if any(
            keyword in message_lower
            for keyword in ["fix", "bug", "critical", "urgent", "security"]
        ):
            multiplier *= 1.5

        # Breaking changes
        if any(
            keyword in message_lower
            for keyword in ["breaking", "break", "remove", "delete"]
        ):
            multiplier *= 1.3

        # New features
        if any(
            keyword in message_lower for keyword in ["feat", "feature", "add", "new"]
        ):
            multiplier *= 1.2

        # Refactoring (often large but less risky)
        if any(
            keyword in message_lower for keyword in ["refactor", "cleanup", "style"]
        ):
            multiplier *= 0.8

        final_score = base_score * multiplier

        # Normalize to 0.0-1.0 range (assuming 100 changes is "high impact")
        return min(final_score / 100.0, 1.0)

    def get_display_summary(self) -> str:
        """Get a formatted summary for display purposes.

        Returns:
            Formatted string suitable for CLI output
        """
        impact = self.calculate_impact_score()
        impact_indicator = "🔥" if impact > 0.7 else "⚡" if impact > 0.3 else "📝"

        # Truncate long messages
        message = self.message.split("\n")[0]  # First line only
        if len(message) > 60:
            message = message[:57] + "..."

        return f"{impact_indicator} {self.short_sha} {message} ({self.author_name})"
