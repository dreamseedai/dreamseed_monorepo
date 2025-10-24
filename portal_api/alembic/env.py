import configparser
import os
import sys
from logging.config import fileConfig
from urllib.parse import quote

from sqlalchemy import pool
from sqlalchemy.engine import create_engine

from alembic import context

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.db import models  # noqa
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _load_db_cfg():
    cfg = {}
    ini_dir = os.path.dirname(config.config_file_name or "alembic.ini")
    local_path = os.path.join(ini_dir, "alembic.ini.local")
    parser = configparser.ConfigParser()
    if os.path.exists(local_path):
        parser.read(local_path)
        if "db" in parser:
            return dict(parser["db"])  # type: ignore
    if config.get_section("db"):
        return dict(config.get_section("db"))  # type: ignore
    return cfg


def _build_sqlalchemy_url() -> str:
    db = _load_db_cfg()
    driver = db.get("driver", "postgresql+psycopg")
    user = db.get("user", "postgres")
    password = quote(db.get("password", ""), safe="")
    host = db.get("host", "127.0.0.1")
    port = db.get("port", "5432")
    name = db.get("name", "postgres")
    return f"{driver}://{user}:{password}@{host}:{port}/{name}"


def run_migrations_offline():
    url = _build_sqlalchemy_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url = _build_sqlalchemy_url()
    connectable = create_engine(url, pool_pre_ping=True, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


