from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from src.core.paths import project_path


# ── Database URL resolution ────────────────────────────────────────────────
# Priority: DATABASE_URL env var (points to Postgres in production)
#           -> falls back to local SQLite for development
_ENV_URL = os.environ.get("DATABASE_URL", "")

if _ENV_URL:
    # Production: PostgreSQL
    DB_PATH = None
    DB_URL = _ENV_URL
    # PostgreSQL uses NullPool in async contexts but QueuePool is fine for sync
    _pool_kwargs: dict = {
        "poolclass": QueuePool,
        "pool_size": 20,
        "max_overflow": 30,
        "pool_pre_ping": True,       # re-validate stale connections automatically
        "pool_recycle": 1800,        # recycle connections every 30 minutes
    }
    _connect_args: dict = {}
else:
    # Development: SQLite (WAL mode for concurrent reads)
    DB_PATH = project_path("data", "mis_store.db")
    DB_URL = f"sqlite:///{DB_PATH.as_posix()}"
    _pool_kwargs = {
        "poolclass": QueuePool,
        "pool_size": 200,
        "max_overflow": 350,
    }
    _connect_args = {"check_same_thread": False, "timeout": 30}


engine = create_engine(DB_URL, connect_args=_connect_args, **_pool_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── SQLite-specific pragmas (WAL mode, busy timeout) ──────────────────────
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    import sqlite3
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


# ── Session helpers ────────────────────────────────────────────────────────
@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class Database:
    def __init__(self, db_url: str = DB_URL):
        is_sqlite = db_url.startswith("sqlite")
        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False, "timeout": 30} if is_sqlite else {},
            poolclass=QueuePool,
            pool_size=200 if is_sqlite else 20,
            max_overflow=350 if is_sqlite else 30,
        )
        self.SessionFactory = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
