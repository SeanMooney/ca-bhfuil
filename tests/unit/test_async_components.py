"""Unit tests for async components."""

import asyncio
import pathlib
import tempfile
from unittest import mock

import httpx
import pytest

from ca_bhfuil.cli import async_bridge
from ca_bhfuil.core import async_config
from ca_bhfuil.core import async_errors
from ca_bhfuil.core import async_monitor
from ca_bhfuil.core import async_progress
from ca_bhfuil.core import async_repository
from ca_bhfuil.core import async_tasks
from ca_bhfuil.core.models import progress
from ca_bhfuil.integrations import async_http
from ca_bhfuil.storage import async_database


@pytest.mark.asyncio
class TestAsyncConfigManager:
    """Test AsyncConfigManager functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Provide temporary config directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield pathlib.Path(tmp_dir)

    async def test_initialization(self, temp_config_dir):
        """Test AsyncConfigManager initialization."""
        manager = async_config.AsyncConfigManager(temp_config_dir)
        assert manager.config_dir == temp_config_dir
        assert manager.repositories_file == temp_config_dir / "repos.yaml"
        assert manager.global_settings_file == temp_config_dir / "global.yaml"
        assert manager.auth_file == temp_config_dir / "auth.yaml"

    async def test_load_configuration_empty(self, temp_config_dir):
        """Test loading configuration when file doesn't exist."""
        manager = async_config.AsyncConfigManager(temp_config_dir)
        config = await manager.load_configuration()
        assert config is not None
        assert hasattr(config, "repos")

    async def test_get_repository_config_none(self, temp_config_dir):
        """Test getting repository config when none exists."""
        manager = async_config.AsyncConfigManager(temp_config_dir)
        result = await manager.get_repository_config("nonexistent")
        assert result is None

    async def test_get_repository_config_by_url_none(self, temp_config_dir):
        """Test getting repository config by URL when none exists."""
        manager = async_config.AsyncConfigManager(temp_config_dir)
        result = await manager.get_repository_config_by_url(
            "https://github.com/user/repo"
        )
        assert result is None

    async def test_validate_configuration_empty(self, temp_config_dir):
        """Test validation with empty configuration."""
        manager = async_config.AsyncConfigManager(temp_config_dir)
        errors = await manager.validate_configuration()
        assert isinstance(errors, list)

    async def test_generate_default_config(self, temp_config_dir):
        """Test generating default configuration files."""
        manager = async_config.AsyncConfigManager(temp_config_dir)
        await manager.generate_default_config()

        assert manager.repositories_file.exists()
        assert manager.global_settings_file.exists()
        assert manager.auth_file.exists()

    async def test_load_auth_config_empty(self, temp_config_dir):
        """Test loading auth config when file doesn't exist."""
        manager = async_config.AsyncConfigManager(temp_config_dir)
        auth_config = await manager.load_auth_config()
        assert auth_config == {}

    async def test_get_auth_method_none(self, temp_config_dir):
        """Test getting auth method when none exists."""
        manager = async_config.AsyncConfigManager(temp_config_dir)
        result = await manager.get_auth_method("nonexistent")
        assert result is None

    async def test_validate_auth_config_empty(self, temp_config_dir):
        """Test validating auth config when file doesn't exist."""
        manager = async_config.AsyncConfigManager(temp_config_dir)
        errors = await manager.validate_auth_config()
        assert isinstance(errors, list)


@pytest.mark.asyncio
class TestAsyncErrorHandler:
    """Test AsyncErrorHandler functionality."""

    async def test_retry_success_first_attempt(self):
        handler = async_errors.AsyncErrorHandler(attempts=3)

        async def succeed():
            return 42

        result = await handler.retry(lambda: succeed(), retry_on=(ValueError,))
        assert result == 42

    async def test_retry_success_after_failures(self):
        handler = async_errors.AsyncErrorHandler(attempts=5)
        attempts = 0

        async def sometimes_fail():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("fail")
            return "ok"

        result = await handler.retry(lambda: sometimes_fail(), retry_on=(ValueError,))
        assert result == "ok"
        assert attempts == 3

    async def test_retry_all_failures(self):
        handler = async_errors.AsyncErrorHandler(attempts=3)

        async def always_fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await handler.retry(lambda: always_fail(), retry_on=(ValueError,))

    async def test_retry_wrong_exception_type(self):
        handler = async_errors.AsyncErrorHandler(attempts=3)

        async def fail_with_type_error():
            raise TypeError("fail")

        with pytest.raises(TypeError):
            await handler.retry(lambda: fail_with_type_error(), retry_on=(ValueError,))


@pytest.mark.asyncio
class TestAsyncOperationMonitor:
    """Test AsyncOperationMonitor functionality."""

    async def test_timed_decorator_success(self):
        """Test timed decorator with successful operation."""
        monitor = async_monitor.AsyncOperationMonitor()

        @monitor.timed
        async def test_operation():
            await asyncio.sleep(0.01)
            return "success"

        result = await test_operation()
        assert result == "success"

        # Check that stats were recorded
        assert "test_operation" in monitor.stats
        stats = monitor.stats["test_operation"]
        assert stats["calls"] == 1
        assert stats["success"] == 1
        assert stats["failure"] == 0
        assert stats["total_duration"] > 0

    async def test_timed_decorator_failure(self):
        """Test timed decorator with failing operation."""
        monitor = async_monitor.AsyncOperationMonitor()

        @monitor.timed
        async def failing_operation():
            await asyncio.sleep(0.01)
            raise ValueError("Test failure")

        with pytest.raises(ValueError, match="Test failure"):
            await failing_operation()

        # Check that stats were recorded
        assert "failing_operation" in monitor.stats
        stats = monitor.stats["failing_operation"]
        assert stats["calls"] == 1
        assert stats["success"] == 0
        assert stats["failure"] == 1
        assert stats["total_duration"] > 0

    async def test_multiple_operations(self):
        """Test monitoring multiple operations."""
        monitor = async_monitor.AsyncOperationMonitor()

        @monitor.timed
        async def operation1():
            await asyncio.sleep(0.01)
            return "success1"

        @monitor.timed
        async def operation2():
            await asyncio.sleep(0.01)
            return "success2"

        await operation1()
        await operation2()

        assert "operation1" in monitor.stats
        assert "operation2" in monitor.stats
        assert monitor.stats["operation1"]["calls"] == 1
        assert monitor.stats["operation2"]["calls"] == 1


@pytest.mark.asyncio
class TestAsyncProgressTracker:
    """Test AsyncProgressTracker functionality."""

    async def test_initialization(self):
        """Test progress tracker initialization."""
        progress_updates = []

        async def progress_callback(progress_obj):
            progress_updates.append(progress_obj)

        tracker = async_progress.AsyncProgressTracker(progress_callback)

        # Verify initialization
        assert tracker._queue is not None
        assert tracker._callback is not None
        assert tracker._consumer_task is not None
        assert not tracker._consumer_task.done()

        # Clean shutdown
        await tracker.shutdown()

    async def test_queue_operations(self):
        """Test queue operations without consumer."""
        progress_updates = []

        async def progress_callback(progress_obj):
            progress_updates.append(progress_obj)

        tracker = async_progress.AsyncProgressTracker(progress_callback)

        # Test queue operations directly
        progress_obj = progress.OperationProgress(
            total=100, completed=50, status="Processing..."
        )

        # Put item in queue
        await tracker._queue.put(progress_obj)
        assert tracker._queue.qsize() == 1

        # Get item from queue
        item = await tracker._queue.get()
        assert item == progress_obj
        tracker._queue.task_done()

        await tracker.shutdown()

    async def test_shutdown_mechanism(self):
        """Test shutdown mechanism."""
        progress_updates = []

        async def progress_callback(progress_obj):
            progress_updates.append(progress_obj)

        tracker = async_progress.AsyncProgressTracker(progress_callback)

        # Shutdown immediately
        await tracker.shutdown()

        # Verify consumer task is cancelled
        assert tracker._consumer_task.cancelled()

    async def test_progress_object_creation(self):
        """Test progress object creation and properties."""
        progress_obj = progress.OperationProgress(
            total=100, completed=50, status="Processing..."
        )

        assert progress_obj.total == 100
        assert progress_obj.completed == 50
        assert progress_obj.status == "Processing..."
        assert progress_obj.percent_complete == 50.0


@pytest.mark.asyncio
class TestAsyncRepositoryManager:
    """Test AsyncRepositoryManager functionality."""

    async def test_concurrent_execution(self):
        """Test concurrent task execution."""
        manager = async_repository.AsyncRepositoryManager(max_concurrent_tasks=2)

        results = []

        async def test_task(task_id):
            await asyncio.sleep(0.01)
            results.append(task_id)
            return f"result_{task_id}"

        tasks = [test_task(1), test_task(2), test_task(3)]

        results_list = await manager.run_concurrently(tasks)

        assert len(results_list) == 3
        assert "result_1" in results_list
        assert "result_2" in results_list
        assert "result_3" in results_list
        assert len(results) == 3

    async def test_concurrent_execution_with_exceptions(self):
        """Test concurrent execution with exceptions."""
        manager = async_repository.AsyncRepositoryManager(max_concurrent_tasks=2)

        async def successful_task():
            await asyncio.sleep(0.01)
            return "success"

        async def failing_task():
            await asyncio.sleep(0.01)
            raise ValueError("Task failed")

        tasks = [successful_task(), failing_task()]

        results = await manager.run_concurrently(tasks)

        assert len(results) == 2
        assert "success" in results
        assert any(isinstance(r, Exception) for r in results)


@pytest.mark.asyncio
class TestAsyncTaskManager:
    """Test AsyncTaskManager functionality."""

    async def test_task_creation_and_status(self):
        """Test creating tasks and checking status."""
        manager = async_tasks.AsyncTaskManager()

        async def test_task():
            await asyncio.sleep(0.01)
            return "task_result"

        task_id = manager.create_task(test_task())

        # Check initial status
        status = manager.get_status(task_id)
        assert status == progress.TaskStatus.RUNNING

        # Wait for completion
        await asyncio.sleep(0.1)

        # Check final status
        status = manager.get_status(task_id)
        assert status == progress.TaskStatus.COMPLETED

        # Get result
        result = manager.get_result(task_id)
        assert result == "task_result"

    async def test_task_failure(self):
        """Test task failure handling."""
        manager = async_tasks.AsyncTaskManager()

        async def failing_task():
            await asyncio.sleep(0.01)
            raise ValueError("Task failed")

        task_id = manager.create_task(failing_task())

        # Wait for completion
        await asyncio.sleep(0.1)

        # Check status
        status = manager.get_status(task_id)
        assert status == progress.TaskStatus.FAILED

        # Get result (should be the exception)
        result = manager.get_result(task_id)
        assert isinstance(result, ValueError)
        assert str(result) == "Task failed"

    async def test_nonexistent_task(self):
        """Test handling of nonexistent task."""
        manager = async_tasks.AsyncTaskManager()

        status = manager.get_status("nonexistent")
        assert status == progress.TaskStatus.PENDING

        result = manager.get_result("nonexistent")
        assert result is None


@pytest.mark.asyncio
class TestAsyncHTTPClient:
    """Test AsyncHTTPClient functionality."""

    async def test_client_initialization(self):
        """Test HTTP client initialization."""
        client = async_http.AsyncHTTPClient(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer token"},
        )

        assert client._base_url == "https://api.example.com"
        assert client._headers["Authorization"] == "Bearer token"

        await client.close()

    async def test_get_request_success(self):
        """Test successful GET request."""
        with mock.patch("httpx.AsyncClient") as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client_class.return_value = mock_client

            mock_response = mock.Mock()
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response

            client = async_http.AsyncHTTPClient()

            response = await client.get("https://api.example.com/test")

            mock_client.get.assert_called_once_with(
                "https://api.example.com/test", params=None
            )
            assert response == mock_response

            await client.close()

    async def test_get_request_with_params(self):
        """Test GET request with parameters."""
        with mock.patch("httpx.AsyncClient") as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client_class.return_value = mock_client

            mock_response = mock.Mock()
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response

            client = async_http.AsyncHTTPClient()

            params = {"page": 1, "limit": 10}
            await client.get("https://api.example.com/test", params=params)

            mock_client.get.assert_called_once_with(
                "https://api.example.com/test", params=params
            )

            await client.close()

    async def test_get_request_http_error(self):
        """Test GET request with HTTP error."""
        with mock.patch("httpx.AsyncClient") as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client_class.return_value = mock_client

            mock_response = mock.Mock()
            real_request = httpx.Request("GET", "https://api.example.com/test")
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=real_request, response=mock_response
            )
            mock_client.get.return_value = mock_response

            client = async_http.AsyncHTTPClient()

            with pytest.raises(httpx.HTTPStatusError):
                await client.get("https://api.example.com/test")

            await client.close()


@pytest.mark.asyncio
class TestAsyncDatabaseManager:
    """Test AsyncDatabaseManager functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Provide temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            yield tmp.name

    async def test_connection_and_execution(self, temp_db_path):
        """Test database connection and execution."""
        manager = async_database.AsyncDatabaseManager(temp_db_path)

        await manager.connect(pool_size=2)

        # Test creating a table
        cursor = await manager.execute(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"
        )
        assert cursor is not None

        # Test inserting data
        cursor = await manager.execute(
            "INSERT INTO test (name) VALUES (?)", ["test_name"]
        )
        assert cursor is not None

        await manager.close()

    async def test_execution_without_connection(self, temp_db_path):
        """Test execution without connecting first."""
        manager = async_database.AsyncDatabaseManager(temp_db_path)

        with pytest.raises(ConnectionError, match="Database not connected"):
            await manager.execute("SELECT 1")

    async def test_connection_pool_management(self, temp_db_path):
        """Test connection pool management."""
        manager = async_database.AsyncDatabaseManager(temp_db_path)

        await manager.connect(pool_size=1)

        # Test that we can execute multiple queries
        await manager.execute("CREATE TABLE test (id INTEGER)")
        await manager.execute("INSERT INTO test (id) VALUES (1)")
        await manager.execute("SELECT * FROM test")

        await manager.close()


@pytest.mark.asyncio
class TestAsyncCLIBridge:
    """Test AsyncCLIBridge functionality."""

    async def test_async_command_decorator_invalid_function(self):
        """Test async_command decorator with invalid function."""

        @async_bridge.async_command
        def invalid_function():
            return "not_async"

        with pytest.raises(TypeError, match="must return a coroutine"):
            invalid_function()

    async def test_with_progress_success(self):
        """Test with_progress function."""

        async def test_operation():
            await asyncio.sleep(0.01)
            return "success"

        result = await async_bridge.with_progress(test_operation(), "Test operation")
        assert result == "success"

    async def test_with_progress_no_progress(self):
        """Test with_progress function with progress disabled."""

        async def test_operation():
            await asyncio.sleep(0.01)
            return "success"

        result = await async_bridge.with_progress(test_operation(), show_progress=False)
        assert result == "success"

    async def test_with_progress_exception(self):
        """Test with_progress function with exception."""

        async def failing_operation():
            raise ValueError("Operation failed")

        with pytest.raises(ValueError, match="Operation failed"):
            await async_bridge.with_progress(failing_operation(), "Failing operation")


class TestCommitModel:
    """Test CommitInfo model functionality."""

    def test_commit_creation(self):
        """Test creating a CommitInfo object."""
        import datetime

        from ca_bhfuil.core.models.commit import CommitInfo

        commit = CommitInfo(
            sha="abc123def456",
            short_sha="abc123d",
            message="Test commit message",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2023, 1, 1, 12, 0, 0),
            committer_name="Test Committer",
            committer_email="committer@example.com",
            committer_date=datetime.datetime(2023, 1, 1, 12, 0, 0),
            files_changed=2,
        )

        assert commit.sha == "abc123def456"
        assert commit.short_sha == "abc123d"
        assert commit.author_name == "Test Author"
        assert commit.author_email == "test@example.com"
        assert commit.files_changed == 2

    def test_commit_validation(self):
        """Test CommitInfo validation."""
        import datetime

        from ca_bhfuil.core.models.commit import CommitInfo

        # Test with minimal required fields
        commit = CommitInfo(
            sha="abc123def456",
            short_sha="abc123d",
            message="Test commit",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2023, 1, 1, 12, 0, 0),
            committer_name="Test Committer",
            committer_email="committer@example.com",
            committer_date=datetime.datetime(2023, 1, 1, 12, 0, 0),
        )

        assert commit.sha == "abc123def456"
        assert commit.parents == []
        assert commit.branches == []
        assert commit.tags == []

    def test_commit_serialization(self):
        """Test CommitInfo serialization."""
        import datetime

        from ca_bhfuil.core.models.commit import CommitInfo

        commit = CommitInfo(
            sha="abc123def456",
            short_sha="abc123d",
            message="Test commit message",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2023, 1, 1, 12, 0, 0),
            committer_name="Test Committer",
            committer_email="committer@example.com",
            committer_date=datetime.datetime(2023, 1, 1, 12, 0, 0),
            files_changed=1,
        )

        # Test dict conversion
        commit_dict = commit.model_dump()
        assert commit_dict["sha"] == "abc123def456"
        assert commit_dict["author_name"] == "Test Author"
        assert commit_dict["files_changed"] == 1

    def test_commit_from_dict(self):
        """Test creating CommitInfo from dictionary."""
        import datetime

        from ca_bhfuil.core.models.commit import CommitInfo

        commit_data = {
            "sha": "abc123def456",
            "short_sha": "abc123d",
            "message": "Test commit message",
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "author_date": datetime.datetime(2023, 1, 1, 12, 0, 0),
            "committer_name": "Test Committer",
            "committer_email": "committer@example.com",
            "committer_date": datetime.datetime(2023, 1, 1, 12, 0, 0),
        }

        commit = CommitInfo.model_validate(commit_data)
        assert commit.sha == "abc123def456"
        assert commit.author_name == "Test Author"

    def test_commit_string_representation(self):
        """Test CommitInfo string representation."""
        import datetime

        from ca_bhfuil.core.models.commit import CommitInfo

        commit = CommitInfo(
            sha="abc123def456",
            short_sha="abc123d",
            message="This is a very long commit message that should be truncated",
            author_name="Test Author",
            author_email="test@example.com",
            author_date=datetime.datetime(2023, 1, 1, 12, 0, 0),
            committer_name="Test Committer",
            committer_email="committer@example.com",
            committer_date=datetime.datetime(2023, 1, 1, 12, 0, 0),
        )

        str_repr = str(commit)
        assert str_repr.startswith("abc123d: This is a very long commit message")
        assert str_repr.endswith("...")
