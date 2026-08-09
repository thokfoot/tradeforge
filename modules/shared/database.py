"""SQLAlchemy engine / session for Postgres-backed stores."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

_engine = None
_SessionLocal: sessionmaker | None = None


def get_engine():
    global _engine
    if _engine is None and settings.database_url:
        _engine = create_engine(
            settings.database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        if engine is None:
            raise RuntimeError("DATABASE_URL not configured — cannot create session.")
        _SessionLocal = sessionmaker(bind=engine)
    return _SessionLocal()


def init_db() -> bool:
    engine = get_engine()
    if engine is None:
        return False
    from modules.shared import models  # noqa: F401
    models.Base.metadata.create_all(bind=engine)
    return True


def use_postgres() -> bool:
    return settings.db_backend == "postgres" and bool(settings.database_url)
