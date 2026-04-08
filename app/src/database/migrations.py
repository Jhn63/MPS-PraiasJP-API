"""Database migration utilities for Alembic."""

from alembic import command  
from alembic.config import Config
import os
from pathlib import Path


def run_alembic_migrations(db_path: str = None) -> None:
    """
    Run all pending Alembic migrations.
    
    Args:
        db_path: Optional path to the alembic.ini file. 
                If not provided, will look for it in the app directory.
    
    This function should be called during application startup to ensure
    all database migrations are applied before the app runs.
    """
    try:
        # Determine the alembic config path
        if db_path is None:
            # Look for alembic.ini relative to current file location
            # The file is in app/src/database/migrations.py
            # So alembic.ini should be in app/alembic.ini
            alembic_ini = Path(__file__).parent.parent.parent / "alembic.ini"
            
            if not alembic_ini.exists():
                print("[Migrations] WARNING: Could not find alembic.ini. Skipping migrations.")
                return
        else:
            alembic_ini = Path(db_path)
        
        # Create Alembic config - ensure it's an absolute path
        config = Config(str(alembic_ini.absolute()))
        
        # Set the database URL from our database module to ensure consistency
        # Use the same absolute path as the app
        from database.db import DATABASE_URL
        config.set_main_option("sqlalchemy.url", DATABASE_URL)
        
        # Run upgrade to latest
        print("[Migrations] Starting Alembic migration upgrade...")
        command.upgrade(config, "head")
        print("[Migrations] ✓ Alembic migrations completed successfully")
        
    except Exception as e:
        print(f"[Migrations] ✗ Error running Alembic migrations: {type(e).__name__}: {e}")
        # Don't raise - allow app to continue even if migrations fail
