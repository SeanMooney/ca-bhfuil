import asyncio
from logging.config import fileConfig
import os
import pathlib

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
import sqlmodel

from ca_bhfuil.core import config as app_config
from ca_bhfuil.storage.database import models  # noqa: F401


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = sqlmodel.SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def do_run_migrations(connection: Connection) -> None:
    """Run migrations in 'online' mode for a given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the database path from environment variable or app config
    env_db_path = os.getenv("CA_BHFUIL_DB_PATH")
    if env_db_path:
        db_path = pathlib.Path(env_db_path)
    else:
        state_dir = app_config.get_state_dir()
        db_path = state_dir / "ca-bhfuil.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)

    connectable = create_async_engine(f"sqlite+aiosqlite:///{db_path}")

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    # Offline mode is not supported for async
    raise NotImplementedError(
        "Offline migration is not supported for this async application."
    )
else:
    asyncio.run(run_migrations_online())
