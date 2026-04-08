from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path

# Use absolute path for database file
DB_PATH = Path(__file__).parent / "base.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    from modules.logger.error_logger import error_logger
    db = SessionLocal()
    try:
        error_logger.info("Database session created")
        yield db
    except Exception as exc:
        error_logger.log_exception(
            exc,
            message="Database session error"
        )
        raise
    finally:
        try:
            db.close()
            error_logger.info("Database session closed")
        except Exception as exc:
            error_logger.log_exception(
                exc,
                message="Error closing database session"
            )
            raise