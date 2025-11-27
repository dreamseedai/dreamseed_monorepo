"""Alembic environment configuration for backend app."""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

# Ensure backend is in sys.path for imports
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy import engine_from_config, pool
from alembic import context

# Import Base metadata for autogenerate
from app.core.database import Base

# Import all models to ensure they are registered with Base
# Import from __init__.py to avoid duplicate table definitions
import app.models  # noqa: F401 - needed for Alembic autogenerate

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from environment or config."""
    # Prefer ALEMBIC_DATABASE_URL (sync driver) over DATABASE_URL (async)
    url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if url:
        # Ensure sync driver (psycopg2) for Alembic
        if "postgresql+asyncpg" in url:
            url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
        return url
    # Fallback to alembic.ini sqlalchemy.url
    return (
        config.get_main_option("sqlalchemy.url")
        or "postgresql://dreamseed_user:dreamseed_pass@localhost:5433/dreamseed_dev"
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get URL and create engine
    url = get_url()

    # Override config with runtime URL
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
