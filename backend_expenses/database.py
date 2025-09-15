# backend_expenses/database.py
import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
from typing import Generator

# --- DB path resolution ---
FINANCE_DB = os.environ.get("FINANCE_DB", None)
if not FINANCE_DB:
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    FINANCE_DB = str(data_dir / "finance.db")

# --- SQLAlchemy setup ---
SQLALCHEMY_DATABASE_URL = f"sqlite:///{FINANCE_DB}"
# check_same_thread=False is required for SQLite + multi-threaded servers
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    """
    FastAPI dependency to yield SQLAlchemy session.
    Use in endpoints: def endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- raw sqlite3 connection helper (for ingest/dedupe scripts) ---
def _ensure_pragmas(conn: sqlite3.Connection) -> None:
    """
    Apply pragmatic SQLite pragmas to improve concurrency/durability.
    """
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        # ignore if pragmas cannot be set yet
        pass

def get_conn() -> sqlite3.Connection:
    """
    Return a configured sqlite3.Connection for lightweight operations.
    Caller must close the connection.
    """
    # Connect with detect_types and allow usage from multiple threads
    conn = sqlite3.connect(FINANCE_DB, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_pragmas(conn)
    return conn

# convenience for scripts
def init_db_schema():
    """
    Call models.Base.metadata.create_all(bind=engine) from outside
    after importing models to create tables.
    """
    from . import models  # local import to avoid top-level cycles
    models.Base.metadata.create_all(bind=engine)
