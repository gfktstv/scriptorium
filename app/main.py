from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqlmodel import SQLModel

import app.models
from app.core.config import settings
from app.db.session import engine
from app.routers import users, repositories, members, objects

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Temporary solution for database initialization (will be replaced with migrations later)
    async with engine.begin() as conn:
        # run_sync executes the synchronous create_all method 
        # using the underlying synchronous driver
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield
    
app = FastAPI(
	title="Scriptorium API",
	version="1.0.0",
	lifespan=lifespan
)

app.include_router(users.router)
app.include_router(repositories.router)
app.include_router(members.router)
app.include_router(objects.router)

if __name__ == "__main__":
	uvicorn.run(
		"app.main:app", 
		port=settings.PORT, 
		host=settings.HOST, 
		reload=True
	)