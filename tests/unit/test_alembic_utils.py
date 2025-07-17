"""Unit tests for alembic testing utilities."""

import pathlib
import tempfile
from unittest import mock

import pytest

from tests.fixtures import alembic


class TestAlembicCommand:
    """Test alembic command execution."""

    @pytest.mark.asyncio
    async def test_run_alembic_command_success(self):
        """Test successful alembic command execution."""
        with mock.patch("asyncio.create_subprocess_shell") as mock_subprocess:
            # Mock successful process
            mock_process = mock.Mock()
            mock_process.returncode = 0
            mock_process.communicate = mock.AsyncMock(return_value=(b"success output", b""))
            mock_subprocess.return_value = mock_process

            return_code, stdout, stderr = await alembic.run_alembic_command("current")

            assert return_code == 0
            assert stdout == "success output"
            assert stderr == ""
            mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_alembic_command_failure(self):
        """Test failed alembic command execution."""
        with mock.patch("asyncio.create_subprocess_shell") as mock_subprocess:
            # Mock failed process
            mock_process = mock.Mock()
            mock_process.returncode = 1
            mock_process.communicate = mock.AsyncMock(return_value=(b"", b"error output"))
            mock_subprocess.return_value = mock_process

            return_code, stdout, stderr = await alembic.run_alembic_command("invalid")

            assert return_code == 1
            assert stdout == ""
            assert stderr == "error output"

    @pytest.mark.asyncio
    async def test_run_alembic_command_with_db_path(self):
        """Test alembic command with database path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = pathlib.Path(tmp_dir) / "test.db"

            with mock.patch("asyncio.create_subprocess_shell") as mock_subprocess:
                mock_process = mock.Mock()
                mock_process.returncode = 0
                mock_process.communicate = mock.AsyncMock(return_value=(b"output", b""))
                mock_subprocess.return_value = mock_process

                await alembic.run_alembic_command("current", db_path)

                # Verify environment variable was set
                call_args = mock_subprocess.call_args
                env = call_args[1]["env"]
                assert "CA_BHFUIL_DB_PATH" in env
                assert env["CA_BHFUIL_DB_PATH"] == str(db_path)

    @pytest.mark.asyncio
    async def test_run_alembic_command_virtual_env_path(self):
        """Test alembic command adds virtual env to PATH."""
        with mock.patch("asyncio.create_subprocess_shell") as mock_subprocess:
            with mock.patch("sys.prefix", "/fake/venv"):
                with mock.patch("sys.base_prefix", "/fake/system"):
                    with mock.patch("pathlib.Path.exists", return_value=True):
                        mock_process = mock.Mock()
                        mock_process.returncode = 0
                        mock_process.communicate = mock.AsyncMock(return_value=(b"", b""))
                        mock_subprocess.return_value = mock_process

                        await alembic.run_alembic_command("current")

                        # Verify PATH was modified
                        call_args = mock_subprocess.call_args
                        env = call_args[1]["env"]
                        assert "/fake/venv/bin" in env["PATH"]


class TestDatabaseCreation:
    """Test database creation utilities."""

    @pytest.mark.asyncio
    async def test_create_test_database_success(self):
        """Test successful test database creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = pathlib.Path(tmp_dir) / "test.db"

            with mock.patch("tests.fixtures.alembic.run_alembic_command") as mock_alembic:
                mock_alembic.return_value = (0, "success", "")

                result_path = await alembic.create_test_database(db_path)

                assert result_path == db_path
                mock_alembic.assert_called_once_with("upgrade head", db_path)

    @pytest.mark.asyncio
    async def test_create_test_database_failure(self):
        """Test failed test database creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = pathlib.Path(tmp_dir) / "test.db"

            with mock.patch("tests.fixtures.alembic.run_alembic_command") as mock_alembic:
                mock_alembic.return_value = (1, "", "migration failed")

                with pytest.raises(RuntimeError, match="Failed to create test database"):
                    await alembic.create_test_database(db_path)

    @pytest.mark.asyncio
    async def test_create_test_database_temporary(self):
        """Test creating temporary database when no path provided."""
        with mock.patch("tests.fixtures.alembic.run_alembic_command") as mock_alembic:
            mock_alembic.return_value = (0, "success", "")

            result_path = await alembic.create_test_database()

            assert result_path.suffix == ".db"
            assert result_path.exists()  # tempfile should create the file
            mock_alembic.assert_called_once_with("upgrade head", result_path)

            # Cleanup
            result_path.unlink()

    @pytest.mark.asyncio
    async def test_reset_test_database(self):
        """Test resetting test database."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = pathlib.Path(tmp_dir) / "test.db"
            db_path.touch()  # Create file

            with mock.patch("tests.fixtures.alembic.create_test_database") as mock_create:
                mock_create.return_value = db_path

                await alembic.reset_test_database(db_path)

                mock_create.assert_called_once_with(db_path)


class TestDatabaseVerification:
    """Test database schema verification."""

    @pytest.mark.asyncio
    async def test_verify_database_schema_success(self):
        """Test successful database schema verification."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = pathlib.Path(tmp_dir) / "test.db"

            with mock.patch("tests.fixtures.alembic.run_alembic_command") as mock_alembic:
                # Mock successful verification
                mock_alembic.side_effect = [
                    (0, "current_revision", ""),  # current command
                    (0, "head_revision", ""),     # heads command
                    (0, "head_revision", ""),     # current command again
                ]

                result = await alembic.verify_database_schema(db_path)

                assert result is True
                assert mock_alembic.call_count == 3

    @pytest.mark.asyncio
    async def test_verify_database_schema_failure(self):
        """Test failed database schema verification."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = pathlib.Path(tmp_dir) / "test.db"

            with mock.patch("tests.fixtures.alembic.run_alembic_command") as mock_alembic:
                # Mock failed verification
                mock_alembic.return_value = (1, "", "error")

                result = await alembic.verify_database_schema(db_path)

                assert result is False

    @pytest.mark.asyncio
    async def test_verify_database_schema_mismatch(self):
        """Test database schema mismatch detection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = pathlib.Path(tmp_dir) / "test.db"

            with mock.patch("tests.fixtures.alembic.run_alembic_command") as mock_alembic:
                # Mock schema mismatch
                mock_alembic.side_effect = [
                    (0, "current_revision", ""),    # current command
                    (0, "head_revision", ""),       # heads command
                    (0, "different_revision", ""),  # current command again
                ]

                result = await alembic.verify_database_schema(db_path)

                assert result is False


class TestDatabaseContext:
    """Test database context manager."""

    @pytest.mark.asyncio
    async def test_database_context_success(self):
        """Test successful database context manager."""
        with mock.patch("tests.fixtures.alembic.create_test_database") as mock_create:
            with mock.patch("pathlib.Path.exists", return_value=True):
                with mock.patch("pathlib.Path.unlink") as mock_unlink:
                    mock_create.return_value = pathlib.Path("/tmp/test.db")

                    async with alembic.test_database_context() as db_path:
                        assert db_path == pathlib.Path("/tmp/test.db")

                    mock_create.assert_called_once()
                    mock_unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_context_no_cleanup(self):
        """Test database context manager without cleanup."""
        with mock.patch("tests.fixtures.alembic.create_test_database") as mock_create:
            with mock.patch("tests.fixtures.alembic.reset_test_database") as mock_reset:
                db_path = pathlib.Path("/tmp/test.db")
                mock_create.return_value = db_path

                async with alembic.test_database_context(db_path, cleanup=False):
                    pass

                mock_create.assert_called_once_with(db_path)
                mock_reset.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_context_reset_on_cleanup(self):
        """Test database context manager resets user-specified database."""
        with mock.patch("tests.fixtures.alembic.create_test_database") as mock_create:
            with mock.patch("tests.fixtures.alembic.reset_test_database") as mock_reset:
                with mock.patch("pathlib.Path.exists", return_value=True):
                    db_path = pathlib.Path("/tmp/test.db")
                    mock_create.return_value = db_path

                    async with alembic.test_database_context(db_path, cleanup=True):
                        pass

                    mock_create.assert_called_once_with(db_path)
                    mock_reset.assert_called_once_with(db_path)


# Note: Fixture tests are not included here as fixtures should be tested
# through their usage in actual test functions rather than being called directly.
