from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from sqlalchemy.orm import Session

from routes.routes import router
from database.db import engine, SessionLocal, Base
from database.migrations import run_alembic_migrations

from modules.logger.logger_service import setup_error_logger, ErrorLoggerMiddleware
from modules.logger.error_logger import error_logger, LogLevel
from modules.monitoring.scheduler import start_monitoring_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    error_logger.info("Error logger initialized")

    # Criar banco com tratamento de erro
    try:
        Base.metadata.create_all(bind=engine)
        error_logger.info("Database tables created or verified")
    except Exception as exc:
        error_logger.log_exception(
            exc,
            message="Failed to create database tables"
        )
        raise
    
    # Run Alembic migrations
    try:
        run_alembic_migrations()
    except Exception as exc:
        error_logger.log_exception(
            exc,
            message="Failed to run database migrations"
        )
        raise

    # Background task
    bg_task = asyncio.create_task(start_monitoring_loop(10800))

    yield

    # Shutdown
    bg_task.cancel()


app = FastAPI(lifespan=lifespan)

# Register middleware BEFORE app starts (before lifespan)
app.add_middleware(ErrorLoggerMiddleware)

# Register exception handlers and other logger setup
setup_error_logger(
    app,
    log_file="logs/errors.log",
    enable_console=True,
    log_format="text",
    min_file_level=LogLevel.ERROR,
    register_handlers=True,
    skip_middleware_registration=True,  # Already added above
)

app.include_router(router)
error_logger.info("Application startup complete")
