from fastapi import FastAPI
from sqlalchemy.orm import Session

from routes.routes import router
from database.db import engine, SessionLocal, Base

from modules.logger.error_logger import LogLevel, error_logger
from modules.logger.logger_service import setup_error_logger

app = FastAPI()

try:
    Base.metadata.create_all(bind=engine)
    error_logger.info("Database tables created or verified")
except Exception as exc:
    error_logger.log_exception(
        exc,
        message="Failed to create database tables"
    )
    raise

setup_error_logger(
    app,
    log_file="logs/errors.log",
    enable_console=True,
    log_format="text",
    min_file_level=LogLevel.ERROR,
)

error_logger.info("Error logger initialized")

app.include_router(router)

error_logger.info("Application startup complete")