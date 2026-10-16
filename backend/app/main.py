from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import get_settings
from app.db.session import Base,engine

@asynccontextmanager
async def lifespan(app):Base.metadata.create_all(engine);yield
app=FastAPI(title="EvalAI API",version="0.1.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=get_settings().origins,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)

