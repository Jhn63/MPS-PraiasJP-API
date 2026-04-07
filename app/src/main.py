from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from sqlalchemy.orm import Session

from routes.routes import router
from database.db import engine, SessionLocal, Base
from modules.monitoring.scheduler import start_monitoring_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    bg_task = asyncio.create_task(start_monitoring_loop(10800))
    
    yield 
    
    bg_task.cancel()

app = FastAPI(lifespan=lifespan)

app.include_router(router)