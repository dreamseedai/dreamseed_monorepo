from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Auto seed control via STAGE env (staging/dev => seed=true)
_stage = os.getenv('STAGE', '').lower()
if _stage in ('staging', 'stage', 'dev', 'development'):
    # Expose an env var for migration scripts to pick up when -x seed= is not provided
    os.environ.setdefault('ALEMBIC_SEED', 'true')

# Allow CI/ops to override DB URL via env var
_db_url = os.getenv('DATABASE_URL')
if _db_url:
    config.set_main_option('sqlalchemy.url', _db_url)

target_metadata = None

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


