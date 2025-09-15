# backend_expenses/database.py
import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from typing import Generator

# Path to SQLite DB file (environment variable or default)
FINANCE_DB = os.environ.get("FINANCE_DB", None)
if not FINANCE_DB:
    # default to repo-relative ./data/finance.db
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    FINANCE_DB = str(data_dir / "finance.db")

# SQLAlchemy engine (for ORM usage)
# Use check_same_thread=False for SQLite + SQLAlchemy in threaded servers
SQLALCHEMY_DATABASE_URL = f"sqlite:///{FINANCE_DB}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Session factory for SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """
    FastAPI dependency: yields a SQLAlchemy session and closes it afterwards.
    Example usage in FastAPI endpoint:
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- raw sqlite3 connection helper (for ingest/dedupe scripts) ---
def _ensure_pragmas(conn: sqlite3.Connection) -> None:
    """
    Apply pragmatic settings to improve concurrency and durability:
    - WAL journal mode (better concurrent readers/writers)
    - synchronous = NORMAL (good tradeoff for speed)
    """
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        # If the DB is not fully initialised yet, ignore pragmas errors
        pass


def get_conn() -> sqlite3.Connection:
    """
    Return a sqlite3.Connection configured for use by scripts that want
    lightweight DB access (ingest service, dedupe functions, raw queries).

    Note: callers are responsible for closing the connection when done.
    """
    # uri mode ensures paths with spaces are handled; detect_types enables types
    conn = sqlite3.connect(FINANCE_DB, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
    # return rows as dict-like objects
    conn.row_factory = sqlite3.Row
    _ensure_pragmas(conn)
    return conn


# Optional helper: initialize DB with SQLAlchemy models if required
def init_db():
    """
    Create tables (uses models.Base.metadata.create_all in other modules).
    Importing models here is optional; typically the app will call:
        models.Base.metadata.create_all(bind=engine)
    """
    # left intentionally minimal; call models.Base.metadata.create_all(bind=engine) from app startup
    pass
