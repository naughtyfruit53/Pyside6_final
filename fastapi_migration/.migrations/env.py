from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine.url import make_url
from alembic import context
import os
import sys
import importlib
import pkgutil

# --- Configure paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# --- Load settings and models ---
try:
    from app.core.config import settings
    from app.core.database import Base
except ImportError as e:
    raise ImportError(f"Could not import app modules: {e}")

models_dir = os.path.join(APP_DIR, "models")
if not os.path.isdir(models_dir):
    raise RuntimeError(f"Models directory not found at {models_dir}")

for (_, module_name, _) in pkgutil.iter_modules([models_dir]):
    importlib.import_module(f"app.models.{module_name}")

# --- Alembic config ---
config = context.config
config.set_main_option(
    'sqlalchemy.url', str(getattr(settings, "DATABASE_URL", ""))
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("DATABASE_URL is not set in app.core.config.settings")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # Safer for SQLite; harmless for Postgres
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # Safer for SQLite; harmless for Postgres
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()