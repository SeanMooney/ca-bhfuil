"""Production alembic interface for database migrations."""

import asyncio
import os
import pathlib
import subprocess
import sys

from loguru import logger


async def run_alembic_upgrade(db_path: pathlib.Path | None = None) -> None:
    """Run alembic upgrade to apply database migrations.

    Args:
        db_path: Optional database path override

    Raises:
        RuntimeError: If alembic upgrade fails
    """
    # Set up environment for alembic to use the specified database
    env = os.environ.copy()
    if db_path:
        # Ensure the database directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # Set environment variable for alembic to use this database
        env["CA_BHFUIL_DB_PATH"] = str(db_path)

    # Add the virtual environment's bin directory to PATH if we're in a virtual env
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        venv_bin = pathlib.Path(sys.prefix) / "bin"
        if venv_bin.exists():
            env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

    # Run alembic upgrade command
    command = "alembic upgrade head"
    logger.debug(f"Running alembic command: {command}")

    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=pathlib.Path.cwd(),  # Ensure we're in the project directory
    )

    stdout_bytes, stderr_bytes = await process.communicate()
    stderr = stderr_bytes.decode() if stderr_bytes else ""

    return_code = process.returncode or 0

    if return_code != 0:
        logger.error(f"Alembic upgrade failed: {stderr}")
        raise RuntimeError(f"Failed to apply database migrations: {stderr}")

    logger.info("Database migrations applied successfully")


async def check_alembic_current(db_path: pathlib.Path | None = None) -> str:
    """Check current alembic revision.

    Args:
        db_path: Optional database path override

    Returns:
        Current revision string

    Raises:
        RuntimeError: If alembic current check fails
    """
    # Set up environment for alembic to use the specified database
    env = os.environ.copy()
    if db_path:
        env["CA_BHFUIL_DB_PATH"] = str(db_path)

    # Add the virtual environment's bin directory to PATH if we're in a virtual env
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        venv_bin = pathlib.Path(sys.prefix) / "bin"
        if venv_bin.exists():
            env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

    # Run alembic current command
    command = "alembic current"
    logger.debug(f"Running alembic command: {command}")

    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=pathlib.Path.cwd(),
    )

    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode() if stdout_bytes else ""
    stderr = stderr_bytes.decode() if stderr_bytes else ""

    return_code = process.returncode or 0

    if return_code != 0:
        logger.error(f"Alembic current check failed: {stderr}")
        raise RuntimeError(f"Failed to check current database revision: {stderr}")

    return stdout.strip()
