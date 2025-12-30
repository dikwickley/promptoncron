from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def _configure_sqlite(dbapi_connection: sqlite3.Connection) -> None:
    # Pragmas for better dev UX / durability.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def create_db_engine() -> Engine:
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
        if isinstance(dbapi_connection, sqlite3.Connection):
            _configure_sqlite(dbapi_connection)

    return engine


ENGINE = create_db_engine()
# expire_on_commit=False prevents ORM instances from being expired after a commit.
# This keeps simple "read then use" patterns safe for our small MVP loops (scheduler/worker).
SessionLocal = sessionmaker(
    bind=ENGINE,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


@contextmanager
def db_session() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


