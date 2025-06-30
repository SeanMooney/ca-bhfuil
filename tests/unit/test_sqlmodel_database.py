"""Unit tests for SQLModel database components."""

import datetime
import pathlib
import tempfile

import pytest

from ca_bhfuil.storage import sqlmodel_manager
from ca_bhfuil.storage.database import engine
from ca_bhfuil.storage.database import models
from ca_bhfuil.storage.database import repository
from ca_bhfuil.testing import alembic_utils


@pytest.mark.asyncio
class TestSQLModelEngine:
    """Test SQLModel database engine functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Provide temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            yield pathlib.Path(tmp.name)

    async def test_engine_initialization(self, temp_db_path):
        """Test database engine initialization."""
        db_engine = engine.DatabaseEngine(temp_db_path)

        # Test engine properties
        assert db_engine.db_path == temp_db_path
        assert "sqlite+aiosqlite" in db_engine.database_url

        # Test schema creation with alembic
        await alembic_utils.create_test_database(temp_db_path)

        # Test session creation
        async with db_engine.get_session() as session:
            assert session is not None

        await db_engine.close()

    async def test_session_context_manager(self, temp_db_path):
        """Test async session context manager."""
        db_engine = engine.DatabaseEngine(temp_db_path)
        await alembic_utils.create_test_database(temp_db_path)

        async with db_engine.get_session() as session:
            # Test we can execute queries
            import sqlalchemy

            result = await session.execute(sqlalchemy.text("SELECT 1"))
            assert result.scalar() == 1

        await db_engine.close()


@pytest.mark.asyncio
class TestSQLModelRepository:
    """Test SQLModel repository pattern functionality."""

    @pytest.fixture
    async def db_session(self):
        """Provide database session for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            temp_path = pathlib.Path(tmp.name)

        # Create database schema with alembic
        await alembic_utils.create_test_database(temp_path)

        db_engine = engine.DatabaseEngine(temp_path)

        async with db_engine.get_session() as session:
            yield session

        await db_engine.close()
        temp_path.unlink()

    async def test_repository_crud_operations(self, db_session):
        """Test repository CRUD operations."""
        repo_manager = repository.RepositoryRepository(db_session)

        # Test create
        repo_data = models.RepositoryCreate(path="/test/path", name="test-repo")
        repo = await repo_manager.create(repo_data)

        assert repo.id is not None
        assert repo.path == "/test/path"
        assert repo.name == "test-repo"
        assert repo.commit_count == 0
        assert repo.branch_count == 0

        # Test get by path
        found_repo = await repo_manager.get_by_path("/test/path")
        assert found_repo is not None
        assert found_repo.id == repo.id

        # Test get by id
        found_by_id = await repo_manager.get_by_id(repo.id)
        assert found_by_id is not None
        assert found_by_id.path == "/test/path"

        # Test update stats
        updated = await repo_manager.update_stats(repo.id, 100, 5)
        assert updated is not None
        assert updated.commit_count == 100
        assert updated.branch_count == 5
        assert updated.last_analyzed is not None

    async def test_commit_crud_operations(self, db_session):
        """Test commit CRUD operations."""
        # First create a repository
        repo_manager = repository.RepositoryRepository(db_session)
        repo_data = models.RepositoryCreate(path="/test/path", name="test-repo")
        repo = await repo_manager.create(repo_data)

        # Now test commit operations
        commit_manager = repository.CommitRepository(db_session)

        # Test create commit
        commit_data = models.CommitCreate(
            repository_id=repo.id,
            sha="abc123def456",
            short_sha="abc123d",
            message="Test commit message",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2024, 1, 1, 12, 0, 0),
            committer_name="Test Committer",
            committer_email="committer@example.com",
            committer_date=datetime.datetime(2024, 1, 1, 12, 0, 0),
            files_changed=3,
            insertions=50,
            deletions=10,
        )
        commit = await commit_manager.create(commit_data)

        assert commit.id is not None
        assert commit.sha == "abc123def456"
        assert commit.short_sha == "abc123d"
        assert commit.message == "Test commit message"
        assert commit.files_changed == 3

        # Test get by SHA
        found_commit = await commit_manager.get_by_sha(repo.id, "abc123def456")
        assert found_commit is not None
        assert found_commit.id == commit.id

        # Test partial SHA lookup
        found_partial = await commit_manager.get_by_sha(repo.id, "abc123d")
        assert found_partial is not None
        assert found_partial.id == commit.id

        # Test search by message pattern
        commits = await commit_manager.find_commits(
            repo.id, message_pattern="Test commit"
        )
        assert len(commits) == 1
        assert commits[0].id == commit.id

    async def test_branch_crud_operations(self, db_session):
        """Test branch CRUD operations."""
        # First create a repository
        repo_manager = repository.RepositoryRepository(db_session)
        repo_data = models.RepositoryCreate(path="/test/path", name="test-repo")
        repo = await repo_manager.create(repo_data)

        # Now test branch operations
        branch_manager = repository.BranchRepository(db_session)

        # Test create branch
        branch_data = models.BranchCreate(
            repository_id=repo.id,
            name="main",
            target_sha="abc123def456",
            is_remote=False,
        )
        branch = await branch_manager.create(branch_data)

        assert branch.id is not None
        assert branch.name == "main"
        assert branch.target_sha == "abc123def456"
        assert branch.is_remote is False

        # Test get by name
        found_branch = await branch_manager.get_by_name(repo.id, "main")
        assert found_branch is not None
        assert found_branch.id == branch.id

        # Test get branches for repository
        branches = await branch_manager.get_by_repository(repo.id)
        assert len(branches) == 1
        assert branches[0].id == branch.id


@pytest.mark.asyncio
class TestSQLModelManager:
    """Test high-level SQLModel database manager."""

    @pytest.fixture
    def temp_db_path(self):
        """Provide temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            yield pathlib.Path(tmp.name)

    async def test_manager_operations(self, temp_db_path):
        """Test SQLModel manager high-level operations."""
        manager = sqlmodel_manager.SQLModelDatabaseManager(temp_db_path)
        await manager.initialize()

        try:
            # Test add repository
            repo_id = await manager.add_repository("/test/path", "test-repo")
            assert isinstance(repo_id, int)
            assert repo_id > 0

            # Test get repository
            repo = await manager.get_repository("/test/path")
            assert repo is not None
            assert repo.name == "test-repo"
            assert repo.path == "/test/path"

            # Test update stats
            await manager.update_repository_stats(repo_id, 50, 3)

            # Verify stats were updated
            updated_repo = await manager.get_repository("/test/path")
            assert updated_repo is not None
            assert updated_repo.commit_count == 50
            assert updated_repo.branch_count == 3

            # Test add commit
            commit_data = {
                "sha": "def456abc123",
                "short_sha": "def456a",
                "message": "Another test commit",
                "author_name": "Another Author",
                "author_email": "another@example.com",
                "author_date": datetime.datetime(2024, 2, 1, 12, 0, 0),
                "committer_name": "Another Committer",
                "committer_email": "committer2@example.com",
                "committer_date": datetime.datetime(2024, 2, 1, 12, 0, 0),
                "files_changed": 2,
                "insertions": 25,
                "deletions": 5,
            }
            commit_id = await manager.add_commit(repo_id, commit_data)
            assert isinstance(commit_id, int)
            assert commit_id > 0

            # Test find commits
            commits = await manager.find_commits(repo_id, sha_pattern="def456")
            assert len(commits) == 1
            assert commits[0].sha == "def456abc123"

            # Test get stats
            stats = await manager.get_stats()
            assert isinstance(stats, dict)
            assert stats["repositories"] >= 1
            assert stats["commits"] >= 1

        finally:
            await manager.close()

    async def test_duplicate_handling(self, temp_db_path):
        """Test handling of duplicate repositories and commits."""
        manager = sqlmodel_manager.SQLModelDatabaseManager(temp_db_path)
        await manager.initialize()

        try:
            # Add repository twice - should return same ID
            repo_id1 = await manager.add_repository("/test/path", "test-repo")
            repo_id2 = await manager.add_repository("/test/path", "test-repo-2")
            assert repo_id1 == repo_id2

            # Add same commit twice - should return same ID
            commit_data = {
                "sha": "duplicate123",
                "short_sha": "dup123",
                "message": "Duplicate commit",
                "author_name": "Author",
                "author_email": "author@example.com",
                "author_date": datetime.datetime(2024, 3, 1, 12, 0, 0),
                "committer_name": "Committer",
                "committer_email": "committer@example.com",
                "committer_date": datetime.datetime(2024, 3, 1, 12, 0, 0),
            }
            commit_id1 = await manager.add_commit(repo_id1, commit_data)
            commit_id2 = await manager.add_commit(repo_id1, commit_data)
            assert commit_id1 == commit_id2

        finally:
            await manager.close()


class TestSQLModelModels:
    """Test SQLModel model validation and functionality."""

    def test_repository_model_validation(self):
        """Test Repository model validation."""
        # Test valid repository
        repo = models.Repository(
            path="/valid/path",
            name="valid-repo",
            commit_count=100,
            branch_count=5,
        )
        assert repo.path == "/valid/path"
        assert repo.name == "valid-repo"
        assert repo.commit_count == 100

        # Test repository create model
        repo_create = models.RepositoryCreate(
            path="/create/path",
            name="create-repo",
        )
        assert repo_create.path == "/create/path"
        assert repo_create.name == "create-repo"

    def test_commit_model_validation(self):
        """Test Commit model validation."""
        commit = models.Commit(
            repository_id=1,
            sha="abc123def456789",
            short_sha="abc123d",
            message="Test commit message",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2024, 1, 1, 12, 0, 0),
            committer_name="Test Committer",
            committer_email="committer@example.com",
            committer_date=datetime.datetime(2024, 1, 1, 12, 0, 0),
        )
        assert commit.repository_id == 1
        assert commit.sha == "abc123def456789"
        assert commit.short_sha == "abc123d"
        assert commit.message == "Test commit message"

    def test_knowledge_graph_models(self):
        """Test knowledge graph model functionality."""
        # Test KGNode model
        node = models.KGNode(
            node_type="commit",
            node_id="abc123",
            properties={"branch": "main", "author": "test"},
        )
        assert node.node_type == "commit"
        assert node.node_id == "abc123"
        assert node.properties["branch"] == "main"

        # Test KGEdge model
        edge = models.KGEdge(
            source_id=1,
            target_id=2,
            edge_type="fixes",
            properties={"confidence": 0.9},
        )
        assert edge.source_id == 1
        assert edge.target_id == 2
        assert edge.edge_type == "fixes"
        assert edge.properties["confidence"] == 0.9

    def test_embedding_record_model(self):
        """Test EmbeddingRecord model functionality."""
        embedding = models.EmbeddingRecord(
            source_type="commit_message",
            source_id="abc123",
            vector_id="vec_001",
            content_hash="hash123",
            metadata_={"model": "ada-002", "dimensions": 1536},
        )
        assert embedding.source_type == "commit_message"
        assert embedding.source_id == "abc123"
        assert embedding.vector_id == "vec_001"
        assert embedding.metadata_["model"] == "ada-002"
