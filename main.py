from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy import text

from src.utils.db import Base,engine
from src.tasks.models import TaskModel
from src.tasks.router import task_routes
from src.user.router import user_routes
from src.admin.router import admin_routes

@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )
    print("Database Connected ✅.")
    yield

app = FastAPI(title="Just touching the cloud",lifespan=lifespan)
app.include_router(task_routes)
app.include_router(user_routes)
app.include_router(admin_routes)
