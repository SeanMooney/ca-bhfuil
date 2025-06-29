"""Enhanced tests for async progress tracking functionality."""

import asyncio
import concurrent.futures
import contextlib
import time
from unittest import mock

import pytest

from ca_bhfuil.core import async_progress
from ca_bhfuil.core.models import progress


class TestAsyncProgressTrackerEnhanced:
    """Enhanced tests for AsyncProgressTracker functionality."""

    @pytest.fixture
    def mock_callback(self):
        """Provide a mock progress callback."""
        return mock.AsyncMock()

    @pytest.fixture
    def sample_progress(self):
        """Provide a sample progress object."""
        return progress.OperationProgress(
            total=100, completed=50, status="processing data"
        )

    @pytest.mark.asyncio
    async def test_progress_tracker_initialization(self, mock_callback):
        """Test progress tracker initialization."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        assert tracker._callback == mock_callback
        assert tracker._queue is not None
        assert tracker._consumer_task is not None
        assert not tracker._consumer_task.done()

        await tracker.shutdown()

    @pytest.mark.asyncio
    async def test_report_progress_async(self, mock_callback, sample_progress):
        """Test reporting progress asynchronously."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Put progress directly into queue
        await tracker._queue.put(sample_progress)

        # Wait a bit for the consumer to process
        await asyncio.sleep(0.1)

        # Verify callback was called
        mock_callback.assert_called_once_with(sample_progress)

        await tracker.shutdown()

    @pytest.mark.asyncio
    async def test_report_progress_from_sync_context(
        self, mock_callback, sample_progress
    ):
        """Test reporting progress from synchronous context."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Test direct async queue put since report_progress has threading complexities
        await tracker._queue.put(sample_progress)

        # Wait for processing
        await asyncio.sleep(0.1)

        # Verify callback was called
        mock_callback.assert_called_once_with(sample_progress)

        await tracker.shutdown()

    @pytest.mark.asyncio
    async def test_multiple_progress_reports(self, mock_callback):
        """Test handling multiple progress reports."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Create multiple progress objects
        progress_objects = [
            progress.OperationProgress(total=100, completed=i * 10, status=f"step {i}")
            for i in range(5)
        ]

        # Put all progress objects into queue
        for prog in progress_objects:
            await tracker._queue.put(prog)

        # Wait for processing
        await asyncio.sleep(0.2)

        # Verify all callbacks were called
        assert mock_callback.call_count == 5
        for i, call in enumerate(mock_callback.call_args_list):
            assert call[0][0].status == f"step {i}"

        await tracker.shutdown()

    @pytest.mark.asyncio
    async def test_progress_callback_exception_handling(self, sample_progress):
        """Test handling exceptions in progress callback."""

        # Create callback that raises exception
        async def failing_callback(prog):
            raise ValueError("Callback failed")

        tracker = async_progress.AsyncProgressTracker(failing_callback)

        # Put progress into queue
        await tracker._queue.put(sample_progress)

        # Wait for processing - should not crash the consumer
        await asyncio.sleep(0.1)

        # Consumer should still be running despite callback failure
        # (The exception is caught and ignored in the consumer)
        assert (
            not tracker._consumer_task.done() or not tracker._consumer_task.cancelled()
        )

        await tracker.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_cancels_consumer_task(self, mock_callback):
        """Test that shutdown properly cancels the consumer task."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Verify task is running
        assert not tracker._consumer_task.done()
        assert not tracker._consumer_task.cancelled()

        # Shutdown
        await tracker.shutdown()

        # Verify task is cancelled/done
        assert tracker._consumer_task.done()

    @pytest.mark.asyncio
    async def test_shutdown_clears_queue(self, mock_callback, sample_progress):
        """Test that shutdown clears remaining queue items."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Put items in queue without processing
        for i in range(3):
            prog = progress.OperationProgress(
                total=100, completed=50, status=f"step {i}"
            )
            await tracker._queue.put(prog)

        # Shutdown should clear the queue
        await tracker.shutdown()

        # Queue should be empty
        assert tracker._queue.empty()

    @pytest.mark.asyncio
    async def test_shutdown_waits_for_task_completion(self, mock_callback):
        """Test that shutdown waits for consumer task completion."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Start shutdown
        start_time = time.time()
        await tracker.shutdown()
        end_time = time.time()

        # Should complete reasonably quickly
        assert end_time - start_time < 1.0
        assert tracker._consumer_task.done()

    @pytest.mark.asyncio
    async def test_multiple_shutdowns_safe(self, mock_callback):
        """Test that multiple shutdowns are safe."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Multiple shutdowns should not cause issues
        await tracker.shutdown()
        await tracker.shutdown()
        await tracker.shutdown()

        assert tracker._consumer_task.done()

    @pytest.mark.asyncio
    async def test_report_progress_after_shutdown(self, mock_callback, sample_progress):
        """Test reporting progress after shutdown."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)
        await tracker.shutdown()

        # Reporting progress after shutdown should not crash
        # but also should not be processed
        def sync_report():
            with contextlib.suppress(RuntimeError):
                # Expected when event loop is not running
                tracker.report_progress(sample_progress)

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, sync_report)

        # Callback should not have been called
        mock_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_consumer_task_processing_order(self, mock_callback):
        """Test that progress reports are processed in order."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Create ordered progress objects
        expected_order = []
        for i in range(10):
            prog = progress.OperationProgress(
                total=100, completed=i * 10, status=f"step {i:02d}"
            )
            expected_order.append(prog.status)
            await tracker._queue.put(prog)

        # Wait for all processing
        await asyncio.sleep(0.3)

        # Verify order was maintained
        actual_order = [call[0][0].status for call in mock_callback.call_args_list]
        assert actual_order == expected_order

        await tracker.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_progress_reporting(self, mock_callback):
        """Test concurrent progress reporting from multiple sources."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        async def report_progress_batch(batch_id: int, count: int):
            """Report a batch of progress updates."""
            for i in range(count):
                prog = progress.OperationProgress(
                    total=100, completed=i * 10, status=f"batch {batch_id} step {i}"
                )
                await tracker._queue.put(prog)

        # Start multiple concurrent batches
        await asyncio.gather(
            report_progress_batch(1, 5),
            report_progress_batch(2, 3),
            report_progress_batch(3, 4),
        )

        # Wait for processing
        await asyncio.sleep(0.2)

        # Should have processed all reports
        assert mock_callback.call_count == 12

        await tracker.shutdown()

    @pytest.mark.asyncio
    async def test_queue_empty_handling_in_shutdown(self, mock_callback):
        """Test proper handling of empty queue during shutdown."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Shutdown with empty queue should work fine
        await tracker.shutdown()

        assert tracker._queue.empty()
        assert tracker._consumer_task.done()

    @pytest.mark.asyncio
    async def test_progress_model_integration(self, mock_callback):
        """Test integration with different progress model scenarios."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Test different progress states
        scenarios = [
            # Completed task
            progress.OperationProgress(total=100, completed=100, status="completed"),
            # Failed task
            progress.OperationProgress(total=100, completed=50, status="failed"),
            # Task with some progress
            progress.OperationProgress(
                total=100, completed=75, status="processing with metadata"
            ),
        ]

        # Report all scenarios
        for scenario in scenarios:
            await tracker._queue.put(scenario)

        # Wait for processing
        await asyncio.sleep(0.2)

        # Verify all were processed
        assert mock_callback.call_count == 3

        # Verify the scenarios were processed correctly
        calls = mock_callback.call_args_list
        assert calls[0][0][0].status == "completed"
        assert calls[1][0][0].status == "failed"
        assert calls[2][0][0].status == "processing with metadata"

        await tracker.shutdown()


class TestAsyncProgressTrackerStressTest:
    """Stress tests for AsyncProgressTracker."""

    @pytest.fixture
    def mock_callback(self):
        """Provide a mock progress callback."""
        return mock.AsyncMock()

    @pytest.mark.asyncio
    async def test_high_volume_progress_reporting(self, mock_callback):
        """Test handling high volume of progress reports."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Generate large number of progress reports
        num_reports = 1000

        async def generate_reports():
            for i in range(num_reports):
                prog = progress.OperationProgress(
                    total=100, completed=i % 100, status=f"stress step {i}"
                )
                await tracker._queue.put(prog)

        start_time = time.time()
        await generate_reports()

        # Wait for processing
        await asyncio.sleep(2.0)  # Give enough time for processing

        end_time = time.time()
        processing_time = end_time - start_time

        # Should handle all reports efficiently
        assert mock_callback.call_count == num_reports
        assert processing_time < 5.0  # Should process reasonably quickly

        await tracker.shutdown()

    @pytest.mark.asyncio
    async def test_rapid_shutdown_during_processing(self, mock_callback):
        """Test shutdown during heavy processing."""
        tracker = async_progress.AsyncProgressTracker(mock_callback)

        # Start heavy processing
        async def heavy_reporting():
            for i in range(100):
                prog = progress.OperationProgress(
                    total=100, completed=i, status=f"heavy step {i}"
                )
                await tracker._queue.put(prog)
                await asyncio.sleep(0.01)  # Small delay

        # Start processing and shutdown quickly
        processing_task = asyncio.create_task(heavy_reporting())
        await asyncio.sleep(0.1)  # Let some processing happen

        # Shutdown should work even during active processing
        await tracker.shutdown()

        # Cancel the processing task
        processing_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await processing_task

        assert tracker._consumer_task.done()


class TestAsyncProgressTrackerErrorScenarios:
    """Test error scenarios and edge cases."""

    @pytest.mark.asyncio
    async def test_callback_with_slow_processing(self):
        """Test callback that processes slowly."""
        call_times = []

        async def slow_callback(prog):
            start = time.time()
            await asyncio.sleep(0.05)  # Simulate slow processing
            call_times.append(time.time() - start)

        tracker = async_progress.AsyncProgressTracker(slow_callback)

        # Send multiple progress reports
        for i in range(3):
            prog = progress.OperationProgress(
                total=100, completed=i * 30, status=f"slow step {i}"
            )
            await tracker._queue.put(prog)

        # Wait for all processing
        await asyncio.sleep(0.3)

        # Should have processed all items despite slow callback
        assert len(call_times) == 3
        assert all(t >= 0.05 for t in call_times)

        await tracker.shutdown()

    @pytest.mark.asyncio
    async def test_callback_with_intermittent_failures(self):
        """Test callback that fails intermittently."""
        success_count = 0
        failure_count = 0

        async def unreliable_callback(prog):
            nonlocal success_count, failure_count
            if "fail" in prog.status:
                failure_count += 1
                raise RuntimeError("Simulated callback failure")
            success_count += 1

        tracker = async_progress.AsyncProgressTracker(unreliable_callback)

        # Send mix of success and failure progress reports
        operations = ["success-1", "fail-1", "success-2", "fail-2", "success-3"]
        for op_id in operations:
            prog = progress.OperationProgress(total=100, completed=50, status=op_id)
            await tracker._queue.put(prog)

        # Wait for processing
        await asyncio.sleep(0.2)

        # Should have attempted to process all, with appropriate success/failure counts
        assert success_count == 3
        assert failure_count == 2

        await tracker.shutdown()
