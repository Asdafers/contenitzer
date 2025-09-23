from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from contextlib import contextmanager
import logging

from ..models import Base  # This will import all models

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./contentizer.db")

# Create engine based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL logging
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_tables():
    """Drop all database tables (use with caution!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


@contextmanager
def get_db_session():
    """Get database session with automatic cleanup"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        logger.error(f"Failed to create database session: {e}")
        raise


class DatabaseManager:
    """Database management utilities"""

    @staticmethod
    def init_db():
        """Initialize database with tables"""
        try:
            create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    @staticmethod
    def reset_db():
        """Reset database (drop and recreate tables)"""
        try:
            drop_tables()
            create_tables()
            logger.info("Database reset successfully")
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            raise

    @staticmethod
    def health_check() -> bool:
        """Check database connection health"""
        try:
            with get_db_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    @staticmethod
    def get_connection_info() -> dict:
        """Get database connection information"""
        return {
            "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,  # Hide credentials
            "engine": str(engine.url.drivername),
            "pool_size": getattr(engine.pool, "size", None),
            "checked_out": getattr(engine.pool, "checkedout", None),
        }


# Initialize database on module import for development
if os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true":
    try:
        create_tables()
    except Exception as e:
        logger.warning(f"Auto table creation failed: {e}")