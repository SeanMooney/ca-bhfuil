"""Tests for enhanced CommitInfo business logic and conversion methods."""

import datetime

import pytest

from ca_bhfuil.core.models import commit as commit_models
from ca_bhfuil.storage.database import models as db_models


class TestCommitInfoConversions:
    """Test conversion methods between business and database models."""

    @pytest.fixture
    def sample_commit_info(self) -> commit_models.CommitInfo:
        """Provide a sample CommitInfo instance."""
        return commit_models.CommitInfo(
            sha="abc123def456789abc123def456789abc123def4",
            short_sha="abc123d",
            message="feat: Add new feature with tests",
            author_name="John Doe",
            author_email="john@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="John Doe",
            committer_email="john@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            parents=["parent1sha", "parent2sha"],
            branches=["main", "feature-branch"],
            tags=["v1.0.0"],
            files_changed=5,
            insertions=150,
            deletions=20,
        )

    @pytest.fixture
    def sample_db_commit(self) -> db_models.Commit:
        """Provide a sample database Commit instance."""
        return db_models.Commit(
            id=1,
            repository_id=100,
            sha="abc123def456789abc123def456789abc123def4",
            short_sha="abc123d",
            message="feat: Add new feature with tests",
            author_name="John Doe",
            author_email="john@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="John Doe",
            committer_email="john@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            files_changed=5,
            insertions=150,
            deletions=20,
        )

    def test_to_db_create_conversion(self, sample_commit_info):
        """Test conversion from CommitInfo to CommitCreate."""
        repository_id = 100

        db_create = sample_commit_info.to_db_create(repository_id)

        assert isinstance(db_create, db_models.CommitCreate)
        assert db_create.repository_id == repository_id
        assert db_create.sha == sample_commit_info.sha
        assert db_create.short_sha == sample_commit_info.short_sha
        assert db_create.message == sample_commit_info.message
        assert db_create.author_name == sample_commit_info.author_name
        assert db_create.author_email == sample_commit_info.author_email
        assert db_create.author_date == sample_commit_info.author_date
        assert db_create.committer_name == sample_commit_info.committer_name
        assert db_create.committer_email == sample_commit_info.committer_email
        assert db_create.committer_date == sample_commit_info.committer_date
        assert db_create.files_changed == sample_commit_info.files_changed
        assert db_create.insertions == sample_commit_info.insertions
        assert db_create.deletions == sample_commit_info.deletions

    def test_from_db_model_conversion(self, sample_db_commit):
        """Test conversion from database Commit to CommitInfo."""
        commit_info = commit_models.CommitInfo.from_db_model(sample_db_commit)

        assert isinstance(commit_info, commit_models.CommitInfo)
        assert commit_info.sha == sample_db_commit.sha
        assert commit_info.short_sha == sample_db_commit.short_sha
        assert commit_info.message == sample_db_commit.message
        assert commit_info.author_name == sample_db_commit.author_name
        assert commit_info.author_email == sample_db_commit.author_email
        assert commit_info.author_date == sample_db_commit.author_date
        assert commit_info.committer_name == sample_db_commit.committer_name
        assert commit_info.committer_email == sample_db_commit.committer_email
        assert commit_info.committer_date == sample_db_commit.committer_date
        assert commit_info.files_changed == sample_db_commit.files_changed
        assert commit_info.insertions == sample_db_commit.insertions
        assert commit_info.deletions == sample_db_commit.deletions

        # Relationship fields should be empty (not stored directly)
        assert commit_info.parents == []
        assert commit_info.branches == []
        assert commit_info.tags == []

    def test_conversion_roundtrip_preserves_core_data(self, sample_commit_info):
        """Test that converting to DB and back preserves core commit data."""
        repository_id = 100

        # Convert to database model and back
        db_create = sample_commit_info.to_db_create(repository_id)

        # Simulate database storage (create a Commit from CommitCreate)
        db_commit = db_models.Commit(
            id=1,
            repository_id=db_create.repository_id,
            sha=db_create.sha,
            short_sha=db_create.short_sha,
            message=db_create.message,
            author_name=db_create.author_name,
            author_email=db_create.author_email,
            author_date=db_create.author_date,
            committer_name=db_create.committer_name,
            committer_email=db_create.committer_email,
            committer_date=db_create.committer_date,
            files_changed=db_create.files_changed,
            insertions=db_create.insertions,
            deletions=db_create.deletions,
        )

        # Convert back to business model
        converted_back = commit_models.CommitInfo.from_db_model(db_commit)

        # Core commit data should be preserved
        assert converted_back.sha == sample_commit_info.sha
        assert converted_back.message == sample_commit_info.message
        assert converted_back.author_name == sample_commit_info.author_name
        assert converted_back.author_date == sample_commit_info.author_date
        assert converted_back.files_changed == sample_commit_info.files_changed

        # Note: parents, branches, tags are not preserved as they're relationship data

    def test_to_db_create_with_none_values(self):
        """Test conversion handles None values properly."""
        commit_info = commit_models.CommitInfo(
            sha="abc123def456789abc123def456789abc123def4",
            short_sha="abc123d",
            message="Simple commit",
            author_name="Jane Doe",
            author_email="jane@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="Jane Doe",
            committer_email="jane@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            # Leave change stats as None
            files_changed=None,
            insertions=None,
            deletions=None,
        )

        db_create = commit_info.to_db_create(200)

        assert db_create.files_changed is None
        assert db_create.insertions is None
        assert db_create.deletions is None


class TestCommitInfoBusinessLogic:
    """Test business logic methods in CommitInfo."""

    @pytest.fixture
    def feature_commit(self) -> commit_models.CommitInfo:
        """Provide a feature commit for testing."""
        return commit_models.CommitInfo(
            sha="feature123",
            short_sha="feat123",
            message="feat: Add user authentication system",
            author_name="Alice Developer",
            author_email="alice@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="Alice Developer",
            committer_email="alice@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            files_changed=8,
            insertions=200,
            deletions=10,
        )

    @pytest.fixture
    def bugfix_commit(self) -> commit_models.CommitInfo:
        """Provide a bug fix commit for testing."""
        return commit_models.CommitInfo(
            sha="bugfix456",
            short_sha="bug456",
            message="fix: Critical security vulnerability in auth",
            author_name="Bob Security",
            author_email="bob@example.com",
            author_date=datetime.datetime(2024, 1, 16, 14, 20, 0),
            committer_name="Bob Security",
            committer_email="bob@example.com",
            committer_date=datetime.datetime(2024, 1, 16, 14, 20, 0),
            files_changed=3,
            insertions=50,
            deletions=30,
        )

    @pytest.fixture
    def refactor_commit(self) -> commit_models.CommitInfo:
        """Provide a refactor commit for testing."""
        return commit_models.CommitInfo(
            sha="refactor789",
            short_sha="ref789",
            message="refactor: Clean up user service code",
            author_name="Charlie Cleaner",
            author_email="charlie@example.com",
            author_date=datetime.datetime(2024, 1, 17, 9, 15, 0),
            committer_name="Charlie Cleaner",
            committer_email="charlie@example.com",
            committer_date=datetime.datetime(2024, 1, 17, 9, 15, 0),
            files_changed=12,
            insertions=300,
            deletions=250,
        )

    def test_matches_pattern_message(self, feature_commit):
        """Test pattern matching in commit message."""
        assert feature_commit.matches_pattern("authentication")
        assert feature_commit.matches_pattern("AUTH")  # Case insensitive
        assert feature_commit.matches_pattern("user")
        assert not feature_commit.matches_pattern("database")

    def test_matches_pattern_author(self, feature_commit):
        """Test pattern matching in author fields."""
        assert feature_commit.matches_pattern("Alice")
        assert feature_commit.matches_pattern("alice@example")
        assert feature_commit.matches_pattern("Developer")
        assert not feature_commit.matches_pattern("Bob")

    def test_matches_pattern_empty_pattern(self, feature_commit):
        """Test pattern matching with empty pattern."""
        assert feature_commit.matches_pattern("")  # Empty string matches everything

    def test_calculate_impact_score_feature(self, feature_commit):
        """Test impact score calculation for feature commit."""
        score = feature_commit.calculate_impact_score()

        # Should be > 0 and apply feature multiplier
        assert score > 0.0
        assert score <= 1.0
        # 8 files + 200 insertions = 208, * 1.2 (feature) = 249.6, / 100 = 2.496, min(2.496, 1.0) = 1.0
        assert score == 1.0

    def test_calculate_impact_score_bugfix(self, bugfix_commit):
        """Test impact score calculation for bug fix commit."""
        score = bugfix_commit.calculate_impact_score()

        # Should apply critical/security multipliers
        assert score > 0.0
        assert score <= 1.0
        # 3 files + 50 insertions = 53, * 1.5 (fix/security) = 79.5, / 100 = 0.795
        assert score == 0.795

    def test_calculate_impact_score_refactor(self, refactor_commit):
        """Test impact score calculation for refactor commit."""
        score = refactor_commit.calculate_impact_score()

        # Should apply refactor reduction multiplier
        assert score > 0.0
        assert score <= 1.0
        # 12 files + 300 insertions = 312, * 0.8 (refactor) = 249.6, / 100 = 2.496, min = 1.0
        assert score == 1.0

    def test_calculate_impact_score_no_stats(self):
        """Test impact score calculation with no change statistics."""
        commit = commit_models.CommitInfo(
            sha="nostats",
            short_sha="nostats",
            message="Simple message",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="Test Author",
            committer_email="test@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            files_changed=None,
            insertions=None,
            deletions=None,
        )

        score = commit.calculate_impact_score()
        assert score == 0.0

    def test_calculate_impact_score_small_change(self):
        """Test impact score calculation for small change."""
        commit = commit_models.CommitInfo(
            sha="small",
            short_sha="small",
            message="docs: Fix typo in README",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="Test Author",
            committer_email="test@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            files_changed=1,
            insertions=2,
            deletions=1,
        )

        score = commit.calculate_impact_score()
        assert 0.0 < score < 0.1  # Small change should have low score

    def test_get_display_summary_high_impact(self, bugfix_commit):
        """Test display summary for high impact commit."""
        summary = bugfix_commit.get_display_summary()

        assert "🔥" in summary  # High impact indicator
        assert bugfix_commit.short_sha in summary
        assert "Bob Security" in summary
        assert len(summary) <= 120  # Reasonable length for display

    def test_get_display_summary_medium_impact(self, feature_commit):
        """Test display summary for medium impact commit."""
        # Modify to have medium impact
        feature_commit.files_changed = 2
        feature_commit.insertions = 30

        summary = feature_commit.get_display_summary()

        assert "🔥" in summary or "⚡" in summary  # High or medium impact
        assert feature_commit.short_sha in summary
        assert "Alice Developer" in summary

    def test_get_display_summary_long_message(self):
        """Test display summary truncates long messages."""
        commit = commit_models.CommitInfo(
            sha="longmsg",
            short_sha="longmsg",
            message="This is a very long commit message that should be truncated when displayed in the summary to prevent it from making the output too wide for normal terminal display",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="Test Author",
            committer_email="test@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            files_changed=1,
            insertions=5,
            deletions=0,
        )

        summary = commit.get_display_summary()

        assert "..." in summary  # Should be truncated
        assert len(summary) <= 120  # Should be reasonable length

    def test_get_display_summary_multiline_message(self):
        """Test display summary uses only first line of multiline message."""
        commit = commit_models.CommitInfo(
            sha="multiline",
            short_sha="multi",
            message="feat: Add new feature\n\nThis is a detailed description\nwith multiple lines of text",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            committer_name="Test Author",
            committer_email="test@example.com",
            committer_date=datetime.datetime(2024, 1, 15, 10, 30, 0),
            files_changed=3,
            insertions=50,
            deletions=10,
        )

        summary = commit.get_display_summary()

        assert "feat: Add new feature" in summary
        assert "detailed description" not in summary  # Second line should not appear
