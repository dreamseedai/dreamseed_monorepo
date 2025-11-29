from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add app directory to path so we can import models
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Import Base and all models for autogenerate support
from app.database import Base
from app.models.user import User
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.progress import Progress

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url from environment if available
# Note: We handle the actual connection in run_migrations functions
# to avoid ConfigParser interpolation issues with @ symbols in password
db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:DreamSeedAi%400908@127.0.0.1:5432/dreamseed')

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Get database URL directly in offline mode to avoid ConfigParser interpolation issues
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        db_url = 'postgresql+psycopg2://postgres:DreamSeedAi%400908@127.0.0.1:5432/dreamseed'
    
    context.configure(
        url=db_url,
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
    # Get database URL directly to avoid ConfigParser interpolation issues
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        db_url = 'postgresql+psycopg2://postgres:DreamSeedAi@0908@127.0.0.1:5432/dreamseed'
    
    # Create engine directly with our URL
    from sqlalchemy import create_engine
    connectable = create_engine(db_url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
