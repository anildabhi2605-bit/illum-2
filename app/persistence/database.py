"""Database engine configuration, WAL lifecycle, and connection pragmas for ILLUM AI STUDIO (P03-T02).

Governed by:
- ADR-001: SQLite local database at data/illum.db
- WAL mode configured once during initialization
- Connection-level pragmas: foreign_keys, busy_timeout, synchronous
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.persistence.models import SCHEMA_SQL_DDL

DEFAULT_DB_PATH = Path("data/illum.db")

try:
    from sqlalchemy import Engine, create_engine, event
    from sqlalchemy.orm import sessionmaker

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    Engine = Any  # type: ignore[assignment,misc]


def configure_database_wal(db_path: Path) -> None:
    """Configure and verify WAL journal mode once during database setup/migration."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        result = cursor.fetchone()
        active_mode = str(result[0]).lower() if result else "unknown"
        if active_mode != "wal":
            raise RuntimeError(f"Failed to enable SQLite WAL mode; active mode is '{active_mode}'.")


def set_connection_pragmas(dbapi_connection: Any) -> None:
    """Enforce connection-level pragmas on SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.close()


def create_sqlite_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create a raw sqlite3 connection with standard pragmas configured."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    set_connection_pragmas(conn)
    return conn


def init_database_tables(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Initialize all 7 core tables, indexes, and constraints from schema DDL."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        set_connection_pragmas(conn)
        cursor = conn.cursor()
        cursor.executescript(SCHEMA_SQL_DDL)
        conn.commit()
    configure_database_wal(db_path)


def get_engine(db_path: Path = DEFAULT_DB_PATH) -> Any:
    """Create and configure a SQLAlchemy Engine with connection pragmas."""
    if not HAS_SQLALCHEMY:
        raise RuntimeError("SQLAlchemy is not installed in the current environment.")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, echo=False)

    @event.listens_for(engine, "connect")
    def _sqlite_connect_listener(dbapi_connection: Any, connection_record: Any) -> None:
        set_connection_pragmas(dbapi_connection)

    return engine


def get_session_factory(engine: Any) -> Any:
    """Create sessionmaker for the given engine."""
    if not HAS_SQLALCHEMY:
        raise RuntimeError("SQLAlchemy is not installed in the current environment.")
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
