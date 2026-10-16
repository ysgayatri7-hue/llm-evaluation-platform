from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings

class Base(DeclarativeBase): pass

def make_engine(url: str | None = None):
    target = url or get_settings().database_url
    kwargs = {"check_same_thread": False} if target.startswith("sqlite") else {}
    return create_engine(target, connect_args=kwargs, pool_pre_ping=True)

engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

