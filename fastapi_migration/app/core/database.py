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

# Database engine
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

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