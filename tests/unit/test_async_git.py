"""Tests for async git manager functionality."""

import asyncio
import concurrent.futures
import time

import pytest

from ca_bhfuil.core.git import async_git


class TestAsyncGitManager:
    """Test AsyncGitManager functionality."""

    def test_async_git_manager_initialization(self):
        """Test async git manager initialization."""
        manager = async_git.AsyncGitManager(max_workers=4)
        assert manager._executor is not None
        assert isinstance(manager._executor, concurrent.futures.ThreadPoolExecutor)
        manager.shutdown()

    def test_async_git_manager_default_initialization(self):
        """Test async git manager initialization with default parameters."""
        manager = async_git.AsyncGitManager()
        assert manager._executor is not None
        assert isinstance(manager._executor, concurrent.futures.ThreadPoolExecutor)
        manager.shutdown()

    @pytest.mark.asyncio
    async def test_run_in_executor_simple_function(self):
        """Test running a simple function in executor."""
        manager = async_git.AsyncGitManager(max_workers=2)

        def simple_func(x: int, y: int) -> int:
            return x + y

        result = await manager.run_in_executor(simple_func, 5, 3)
        assert result == 8
        manager.shutdown()

    @pytest.mark.asyncio
    async def test_run_in_executor_with_no_args(self):
        """Test running a function with no arguments in executor."""
        manager = async_git.AsyncGitManager(max_workers=2)

        def no_args_func() -> str:
            return "hello world"

        result = await manager.run_in_executor(no_args_func)
        assert result == "hello world"
        manager.shutdown()

    @pytest.mark.asyncio
    async def test_run_in_executor_with_multiple_args(self):
        """Test running a function with multiple arguments in executor."""
        manager = async_git.AsyncGitManager(max_workers=2)

        def multi_args_func(a: str, b: int, c: bool, d: float) -> dict:
            return {"a": a, "b": b, "c": c, "d": d}

        result = await manager.run_in_executor(multi_args_func, "test", 42, True, 3.14)
        expected = {"a": "test", "b": 42, "c": True, "d": 3.14}
        assert result == expected
        manager.shutdown()

    @pytest.mark.asyncio
    async def test_run_in_executor_exception_handling(self):
        """Test exception handling in executor."""
        manager = async_git.AsyncGitManager(max_workers=2)

        def failing_func() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await manager.run_in_executor(failing_func)

        manager.shutdown()

    @pytest.mark.asyncio
    async def test_run_in_executor_concurrent_execution(self):
        """Test concurrent execution of multiple functions."""
        manager = async_git.AsyncGitManager(max_workers=3)

        def slow_func(duration: float, value: str) -> str:
            time.sleep(duration)
            return f"completed_{value}"

        # Start multiple concurrent tasks
        tasks = [
            manager.run_in_executor(slow_func, 0.1, "task1"),
            manager.run_in_executor(slow_func, 0.1, "task2"),
            manager.run_in_executor(slow_func, 0.1, "task3"),
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Should complete in roughly parallel time (less than sequential)
        assert end_time - start_time < 0.25  # Should be much less than 0.3 (3 * 0.1)
        assert set(results) == {"completed_task1", "completed_task2", "completed_task3"}
        manager.shutdown()

    @pytest.mark.asyncio
    async def test_run_in_executor_with_callable_object(self):
        """Test running a callable object in executor."""
        manager = async_git.AsyncGitManager(max_workers=2)

        class CallableClass:
            def __init__(self, multiplier: int):
                self.multiplier = multiplier

            def __call__(self, value: int) -> int:
                return value * self.multiplier

        callable_obj = CallableClass(3)
        result = await manager.run_in_executor(callable_obj, 7)
        assert result == 21
        manager.shutdown()

    @pytest.mark.asyncio
    async def test_run_in_executor_lambda_function(self):
        """Test running a lambda function in executor."""
        manager = async_git.AsyncGitManager(max_workers=2)

        def lambda_func(x, y):
            return x * y + 1

        result = await manager.run_in_executor(lambda_func, 4, 5)
        assert result == 21
        manager.shutdown()

    def test_shutdown_closes_executor(self):
        """Test that shutdown properly closes the executor."""
        manager = async_git.AsyncGitManager(max_workers=2)
        executor = manager._executor

        manager.shutdown()

        # After shutdown, the executor should be shut down
        assert executor._shutdown

    def test_shutdown_multiple_calls(self):
        """Test that multiple shutdown calls don't cause issues."""
        manager = async_git.AsyncGitManager(max_workers=2)

        # Should not raise any exceptions
        manager.shutdown()
        manager.shutdown()
        manager.shutdown()

    @pytest.mark.asyncio
    async def test_run_in_executor_after_shutdown(self):
        """Test running executor after shutdown raises appropriate error."""
        manager = async_git.AsyncGitManager(max_workers=2)
        manager.shutdown()

        def simple_func() -> str:
            return "test"

        # Should raise RuntimeError when trying to use shut down executor
        with pytest.raises(RuntimeError):
            await manager.run_in_executor(simple_func)


class TestAsyncGitManagerIntegration:
    """Test AsyncGitManager integration scenarios."""

    @pytest.mark.asyncio
    async def test_git_like_operations_simulation(self):
        """Test simulating git-like operations that would be run in executor."""
        manager = async_git.AsyncGitManager(max_workers=2)

        def simulate_git_log(repo_path: str, limit: int) -> list[str]:
            """Simulate a git log operation."""
            return [f"commit_{i}_in_{repo_path}" for i in range(limit)]

        def simulate_git_status(repo_path: str) -> dict:
            """Simulate a git status operation."""
            return {
                "repo": repo_path,
                "clean": True,
                "staged": [],
                "modified": [],
                "untracked": [],
            }

        # Run multiple git-like operations concurrently
        log_task = manager.run_in_executor(simulate_git_log, "/repo1", 3)
        status_task = manager.run_in_executor(simulate_git_status, "/repo2")

        log_result, status_result = await asyncio.gather(log_task, status_task)

        assert log_result == [
            "commit_0_in_/repo1",
            "commit_1_in_/repo1",
            "commit_2_in_/repo1",
        ]
        assert status_result["repo"] == "/repo2"
        assert status_result["clean"] is True

        manager.shutdown()

    @pytest.mark.asyncio
    async def test_heavy_computation_simulation(self):
        """Test handling of heavy computation in executor."""
        manager = async_git.AsyncGitManager(max_workers=2)

        def heavy_computation(data_size: int) -> int:
            """Simulate heavy computation."""
            result = 0
            for i in range(data_size):
                result += i**2
            return result

        # Test with different data sizes concurrently
        tasks = [
            manager.run_in_executor(heavy_computation, 1000),
            manager.run_in_executor(heavy_computation, 2000),
        ]

        results = await asyncio.gather(*tasks)

        # Verify results are correct
        assert results[0] == sum(i**2 for i in range(1000))
        assert results[1] == sum(i**2 for i in range(2000))

        manager.shutdown()

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure_operations(self):
        """Test handling mixed success and failure operations."""
        manager = async_git.AsyncGitManager(max_workers=3)

        def success_operation(value: str) -> str:
            return f"success_{value}"

        def failure_operation() -> None:
            raise RuntimeError("Operation failed")

        # Mix successful and failing operations
        success_task = manager.run_in_executor(success_operation, "test")
        failure_task = manager.run_in_executor(failure_operation)

        # Successful operation should complete
        success_result = await success_task
        assert success_result == "success_test"

        # Failing operation should raise exception
        with pytest.raises(RuntimeError, match="Operation failed"):
            await failure_task

        manager.shutdown()


class TestAsyncGitManagerEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_max_workers(self):
        """Test initialization with zero max workers."""
        # ThreadPoolExecutor raises ValueError for max_workers <= 0
        with pytest.raises(ValueError, match="max_workers must be greater than 0"):
            async_git.AsyncGitManager(max_workers=0)

    def test_negative_max_workers(self):
        """Test initialization with negative max workers."""
        # ThreadPoolExecutor raises ValueError for max_workers <= 0
        with pytest.raises(ValueError, match="max_workers must be greater than 0"):
            async_git.AsyncGitManager(max_workers=-1)

    @pytest.mark.asyncio
    async def test_run_in_executor_with_none_function(self):
        """Test running None as function raises appropriate error."""
        manager = async_git.AsyncGitManager(max_workers=2)

        with pytest.raises(TypeError):
            await manager.run_in_executor(None)  # type: ignore

        manager.shutdown()

    @pytest.mark.asyncio
    async def test_run_in_executor_with_non_callable(self):
        """Test running non-callable object raises appropriate error."""
        manager = async_git.AsyncGitManager(max_workers=2)

        with pytest.raises(TypeError):
            await manager.run_in_executor("not_a_function")  # type: ignore

        manager.shutdown()

    @pytest.mark.asyncio
    async def test_large_number_of_concurrent_tasks(self):
        """Test handling large number of concurrent tasks."""
        manager = async_git.AsyncGitManager(max_workers=4)

        def simple_task(task_id: int) -> int:
            return task_id * 2

        # Create many concurrent tasks
        tasks = [manager.run_in_executor(simple_task, i) for i in range(50)]

        results = await asyncio.gather(*tasks)

        # Verify all results are correct
        expected = [i * 2 for i in range(50)]
        assert results == expected

        manager.shutdown()


class TestAsyncGitManagerResourceManagement:
    """Test resource management and cleanup."""

    def test_context_manager_like_usage(self):
        """Test proper resource management pattern."""
        # Test that manual management works properly
        manager = async_git.AsyncGitManager(max_workers=2)

        try:
            # Manager should be usable
            assert manager._executor is not None
            assert not manager._executor._shutdown
        finally:
            # Cleanup
            manager.shutdown()
            assert manager._executor._shutdown

    @pytest.mark.asyncio
    async def test_executor_thread_pool_limits(self):
        """Test that thread pool respects max_workers limit."""
        max_workers = 2
        manager = async_git.AsyncGitManager(max_workers=max_workers)

        def get_thread_info() -> str:
            import threading

            return threading.current_thread().name

        # Run more tasks than max_workers to test pooling
        tasks = [manager.run_in_executor(get_thread_info) for _ in range(6)]

        thread_names = await asyncio.gather(*tasks)
        unique_threads = set(thread_names)

        # Should not exceed max_workers threads (plus potential main thread)
        assert len(unique_threads) <= max_workers + 1

        manager.shutdown()
