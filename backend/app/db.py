from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Create any missing tables. Existing tables are left untouched."""
    from app import models  # noqa: F401  (registers the tables on Base.metadata)

    Base.metadata.create_all(bind=engine)


def get_sessionmaker() -> sessionmaker:
    """Background tasks open their own session; injected so tests can override it."""
    return SessionLocal


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
