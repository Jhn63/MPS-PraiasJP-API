from fastapi import FastAPI
from sqlalchemy.orm import Session

from routes.routes import router
from database.db import engine, SessionLocal, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router)