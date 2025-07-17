"""Tests for BaseManager and ManagerRegistry."""

import unittest.mock

import pytest
import sqlalchemy.ext.asyncio

from ca_bhfuil.core.managers import base as base_manager
from ca_bhfuil.core.models import results as result_models
from ca_bhfuil.storage.database import engine as db_engine
from tests.fixtures import alembic


class MockOperationResult(result_models.OperationResult):
    """Mock result for testing base manager functionality."""

    test_data: str = ""


class TestBaseManager:
    """Test BaseManager base class functionality."""

    class ConcreteManager(base_manager.BaseManager):
        """Concrete implementation for testing."""

        async def test_operation(self) -> MockOperationResult:
            """Test operation that uses base manager patterns."""
            async with self._operation_context("test operation") as (
                start_time,
                db_repo,
            ):
                # Simulate some work
                test_data = "operation successful"

                return self._create_success_result(
                    MockOperationResult,
                    start_time,
                    test_data=test_data,
                )

        async def test_operation_with_error(self) -> MockOperationResult:
            """Test operation that raises an error."""
            async with self._operation_context("test error operation") as (
                start_time,
                db_repo,
            ):
                raise ValueError("Simulated error")

        async def test_operation_with_manual_error_handling(
            self,
        ) -> MockOperationResult:
            """Test operation with manual error handling."""
            async with self._operation_context("test manual error") as (
                start_time,
                db_repo,
            ):
                try:
                    raise RuntimeError("Manual error")
                except Exception as e:
                    return self._create_error_result(
                        MockOperationResult,
                        start_time,
                        e,
                        test_data="error handled",
                    )

    @pytest.fixture
    async def db_session(self, tmp_path):
        """Provide a test database session."""
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        test_engine = db_engine.DatabaseEngine(db_path)
        session = sqlalchemy.ext.asyncio.AsyncSession(test_engine.engine)

        yield session

        await session.close()
        await test_engine.close()

    @pytest.fixture
    async def manager(self, db_session):
        """Provide a concrete manager instance."""
        manager = self.ConcreteManager(db_session)
        yield manager
        await manager.close()

    async def test_manager_initialization_with_session(self, db_session):
        """Test manager initialization with provided session."""
        manager = self.ConcreteManager(db_session)

        assert manager._db_session is db_session
        assert manager._session_owned is False

        await manager.close()

    async def test_manager_initialization_without_session(self):
        """Test manager initialization without session."""
        manager = self.ConcreteManager()

        assert manager._db_session is None
        assert manager._session_owned is True

        await manager.close()

    async def test_operation_context_success(self, manager):
        """Test operation context for successful operations."""
        result = await manager.test_operation()

        assert result.success is True
        assert result.duration > 0
        assert result.test_data == "operation successful"
        assert result.error is None

    async def test_operation_context_with_exception(self, manager):
        """Test operation context when exception occurs."""
        with pytest.raises(ValueError, match="Simulated error"):
            await manager.test_operation_with_error()

    async def test_create_success_result(self, manager):
        """Test creating success results with timing."""
        result = await manager.test_operation()

        assert result.success is True
        assert isinstance(result.duration, float)
        assert result.duration > 0
        assert result.test_data == "operation successful"

    async def test_create_error_result(self, manager):
        """Test creating error results with exception details."""
        result = await manager.test_operation_with_manual_error_handling()

        assert result.success is False
        assert isinstance(result.duration, float)
        assert result.duration > 0
        assert result.error == "Manual error"
        assert result.test_data == "error handled"

    async def test_get_db_repository_creates_session(self):
        """Test that _get_db_repository creates session when needed."""
        manager = self.ConcreteManager()

        # Initially no session
        assert manager._db_session is None

        # Getting db repository should create session
        db_repo = await manager._get_db_repository()
        assert db_repo is not None
        assert manager._db_session is not None

        await manager.close()

    async def test_get_db_repository_reuses_session(self, db_session):
        """Test that _get_db_repository reuses existing session."""
        manager = self.ConcreteManager(db_session)

        # Get repository twice
        db_repo1 = await manager._get_db_repository()
        db_repo2 = await manager._get_db_repository()

        # Should reuse the same repository instance
        assert db_repo1 is db_repo2
        assert manager._db_session is db_session

        await manager.close()

    async def test_transaction_context_success(self, manager):
        """Test transaction context for successful operations."""
        async with manager._transaction() as session:
            assert session is not None
            # Transaction should commit automatically

    async def test_transaction_context_with_exception(self, manager):
        """Test transaction context when exception occurs."""
        with pytest.raises(ValueError):
            async with manager._transaction() as session:
                assert session is not None
                # This should trigger rollback
                raise ValueError("Transaction error")

    async def test_close_owned_session(self):
        """Test closing manager that owns its session."""
        manager = self.ConcreteManager()

        # Force creation of session
        await manager._get_db_repository()
        assert manager._db_session is not None

        # Close should clean up
        await manager.close()
        assert manager._db_session is None
        assert manager._db_repository is None

    async def test_close_external_session(self, db_session):
        """Test closing manager with external session."""
        manager = self.ConcreteManager(db_session)

        # Get repository to set up internal state
        await manager._get_db_repository()

        # Close should not close external session
        await manager.close()
        assert manager._db_session is db_session  # External session preserved


class TestManagerRegistry:
    """Test ManagerRegistry for dependency injection."""

    @pytest.fixture
    def registry(self):
        """Provide a manager registry."""
        return base_manager.ManagerRegistry()

    async def test_register_and_get_manager(self, registry):
        """Test registering and retrieving managers."""
        mock_manager = unittest.mock.MagicMock()

        # Register manager
        registry.register(str, mock_manager)

        # Retrieve manager
        retrieved = registry.get(str)
        assert retrieved is mock_manager

    async def test_get_unregistered_manager(self, registry):
        """Test retrieving unregistered manager raises error."""
        with pytest.raises(KeyError, match="Manager type int not registered"):
            registry.get(int)

    @pytest.fixture
    async def db_session(self, tmp_path):
        """Provide a test database session."""
        db_path = tmp_path / "test.db"
        await alembic.create_test_database(db_path)

        test_engine = db_engine.DatabaseEngine(db_path)
        session = sqlalchemy.ext.asyncio.AsyncSession(test_engine.engine)

        yield session

        await session.close()
        await test_engine.close()

    async def test_set_shared_session(self, registry, db_session):
        """Test setting shared session across managers."""
        mock_manager = unittest.mock.MagicMock()
        mock_manager._db_session = None
        mock_manager._db_repository = "old_repo"

        registry.register(str, mock_manager)

        # Set shared session
        await registry.set_shared_session(db_session)

        # Manager should have new session
        assert mock_manager._db_session is db_session
        assert mock_manager._db_repository is None  # Should be reset

    async def test_close_all_managers(self, registry):
        """Test closing all registered managers."""
        mock_manager1 = unittest.mock.AsyncMock()
        mock_manager2 = unittest.mock.AsyncMock()

        registry.register(str, mock_manager1)
        registry.register(int, mock_manager2)

        # Close all
        await registry.close_all()

        # All managers should be closed
        mock_manager1.close.assert_called_once()
        mock_manager2.close.assert_called_once()

        # Registry should be empty
        assert len(registry._managers) == 0

    async def test_close_all_with_session(self, registry, db_session):
        """Test closing registry with shared session."""
        registry._db_session = db_session

        # Mock the session close method
        with unittest.mock.patch.object(
            db_session, "close", new_callable=unittest.mock.AsyncMock
        ) as mock_close:
            await registry.close_all()
            mock_close.assert_called_once()

    async def test_close_all_without_close_method(self, registry):
        """Test closing managers that don't have close method."""
        # Create a simple object without close method
        mock_manager = object()

        registry.register(str, mock_manager)

        # Should not raise error
        await registry.close_all()
        assert len(registry._managers) == 0
