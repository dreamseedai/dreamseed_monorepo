from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure repo root and 'apps' are importable regardless of CWD
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
APPS = os.path.join(ROOT, "apps")
if os.path.isdir(APPS) and APPS not in sys.path:
    sys.path.insert(0, APPS)

# Import Base metadata for autogenerate
try:
    from apps.seedtest_api.db.base import Base  # when running from repo root
    from apps.seedtest_api import models as _models_pkg  # ensure model modules are importable
except Exception:
    # Fallback when PYTHONPATH=apps is used (module name 'seedtest_api')
    from seedtest_api.db.base import Base  # type: ignore
    from seedtest_api import models as _models_pkg  # type: ignore

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata for 'autogenerate' support
# Ensure all model modules are imported so tables are registered on Base
try:
    # Import known model modules explicitly
    from apps.seedtest_api.models import question, topic, result  # noqa: F401
except Exception:
    try:
        from seedtest_api.models import question, topic, result  # type: ignore # noqa: F401
    except Exception:
        pass

target_metadata = Base.metadata


def get_url() -> str:
    # Prefer DATABASE_URL env var; fall back to alembic.ini if present
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        version_table_pk=False,  # Allow longer version strings
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    url = get_url()
    if url:
        configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            version_table_pk=False,  # Allow longer version strings
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
