from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Determine database URL with fallback to SQLite
database_url = settings.DATABASE_URL
if not database_url:
    database_url = "sqlite:///./tritiq_erp.db"
    logger.info("No DATABASE_URL configured, using SQLite: tritiq_erp.db")

# Database engine configuration
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "echo": settings.DEBUG
}

# PostgreSQL/Supabase specific configuration
if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
    })
    logger.info("Using PostgreSQL/Supabase database configuration")
elif database_url.startswith("sqlite://"):
    # SQLite specific configuration
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False}
    })
    logger.info("Using SQLite database configuration")

# Database engine
engine = create_engine(database_url, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)