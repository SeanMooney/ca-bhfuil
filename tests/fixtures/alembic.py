"""Alembic testing fixtures for ca-bhfuil."""

import asyncio
from contextlib import asynccontextmanager
import os
import pathlib
import subprocess
import sys
import tempfile
import typing

from loguru import logger
import pytest


async def run_alembic_command(
    command: str, db_path: pathlib.Path | None = None
) -> tuple[int, str, str]:
    """Run an alembic command for the given database.

    Args:
        command: Alembic command to run (e.g., "upgrade head")
        db_path: Optional database path override

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    # Set up environment for alembic to use the specified database
    env = {}
    if db_path:
        # Ensure the database directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # Set environment variable for alembic to use this database
        env["CA_BHFUIL_DB_PATH"] = str(db_path)

    # Run alembic command with proper environment
    full_command = f"alembic {command}"
    logger.debug(f"Running alembic command: {full_command}")

    # Get the current environment and add the .venv/bin path
    current_env = os.environ.copy()
    if env:
        current_env.update(env)

    # Add the virtual environment's bin directory to PATH if we're in a virtual env
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        venv_bin = pathlib.Path(sys.prefix) / "bin"
        if venv_bin.exists():
            current_env["PATH"] = f"{venv_bin}:{current_env.get('PATH', '')}"

    process = await asyncio.create_subprocess_shell(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=current_env,
        cwd=pathlib.Path.cwd(),  # Ensure we're in the project directory
    )

    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode() if stdout_bytes else ""
    stderr = stderr_bytes.decode() if stderr_bytes else ""

    return_code = process.returncode or 0

    if return_code == 0:
        logger.debug(f"Alembic command succeeded: {command}")
    else:
        logger.error(f"Alembic command failed: {command}, stderr: {stderr}")

    return return_code, stdout, stderr


async def create_test_database(db_path: pathlib.Path | None = None) -> pathlib.Path:
    """Create a test database using alembic migrations.

    Args:
        db_path: Optional specific database path. If None, creates a temporary database.

    Returns:
        Path to the created database

    Raises:
        RuntimeError: If alembic migration fails
    """
    if db_path is None:
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            db_path = pathlib.Path(temp_file.name)

    logger.debug(f"Creating test database at {db_path}")

    # Run alembic upgrade to create schema
    return_code, _stdout, stderr = await run_alembic_command("upgrade head", db_path)

    if return_code != 0:
        raise RuntimeError(f"Failed to create test database: {stderr}")

    logger.info(f"Test database created at {db_path}")
    return db_path


async def reset_test_database(db_path: pathlib.Path) -> None:
    """Reset a test database by dropping and recreating all tables.

    Note: Since we don't support downgrades, this removes the database file
    and recreates it with fresh migrations.

    Args:
        db_path: Path to the database to reset
    """
    logger.debug(f"Resetting test database at {db_path}")

    # Remove the database file if it exists
    if db_path.exists():
        db_path.unlink()

    # Recreate the database
    await create_test_database(db_path)
    logger.info(f"Test database reset at {db_path}")


async def verify_database_schema(db_path: pathlib.Path) -> bool:
    """Verify that the database schema matches alembic migrations.

    Args:
        db_path: Path to the database to verify

    Returns:
        True if schema is current, False otherwise
    """
    return_code, stdout, stderr = await run_alembic_command("current", db_path)

    if return_code != 0:
        logger.error(f"Failed to check database schema: {stderr}")
        return False

    # Check if we're at the head revision
    return_code, stdout, stderr = await run_alembic_command("heads", db_path)
    if return_code != 0:
        logger.error(f"Failed to get head revision: {stderr}")
        return False

    head_revision = stdout.strip()

    # Get current revision
    return_code, stdout, stderr = await run_alembic_command("current", db_path)
    if return_code != 0:
        return False

    current_revision = stdout.strip()

    is_current = head_revision in current_revision
    if not is_current:
        logger.warning(
            f"Database schema is not current. Head: {head_revision}, Current: {current_revision}"
        )

    return is_current


@asynccontextmanager
async def test_database_context(
    db_path: pathlib.Path | None = None, cleanup: bool = True
) -> typing.AsyncGenerator[pathlib.Path, None]:
    """Context manager for test databases with automatic cleanup.

    Args:
        db_path: Optional specific database path. If None, creates temporary database.
        cleanup: Whether to clean up the database on exit

    Yields:
        Path to the test database
    """
    created_temp_db = db_path is None

    try:
        db_path = await create_test_database(db_path)
        yield db_path
    finally:
        if cleanup and db_path and db_path.exists():
            if created_temp_db:
                # Remove temporary database file
                db_path.unlink()
                logger.debug(f"Cleaned up temporary test database: {db_path}")
            else:
                # Reset user-specified database
                await reset_test_database(db_path)


@pytest.fixture
async def temp_alembic_database():
    """Pytest fixture for temporary alembic database.

    Creates a temporary database with alembic migrations applied,
    automatically cleaning up after the test.

    Returns:
        Path to the temporary database file
    """
    async with test_database_context() as db_path:
        yield db_path


@pytest.fixture
async def persistent_alembic_database(tmp_path):
    """Pytest fixture for persistent alembic database in temp directory.

    Creates a database in the pytest temp directory with alembic migrations applied.
    Database is automatically cleaned up by pytest's tmp_path fixture.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to the database file
    """
    db_path = tmp_path / "test.db"
    async with test_database_context(db_path, cleanup=False) as db_path:
        yield db_path


@pytest.fixture
async def verified_alembic_database():
    """Pytest fixture for verified alembic database.

    Creates a temporary database and verifies the schema matches
    the current alembic migrations.

    Returns:
        Path to the verified database file
    """
    async with test_database_context() as db_path:
        is_current = await verify_database_schema(db_path)
        if not is_current:
            raise RuntimeError("Database schema verification failed")
        yield db_path
