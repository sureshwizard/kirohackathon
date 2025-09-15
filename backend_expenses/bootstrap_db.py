#!/usr/bin/env python3
"""
bootstrap_db.py

Create the SQLite database file and all tables declared in backend_expenses.models.
Run this once before running the app (or any time you need to recreate missing tables).
"""

import sys
from pathlib import Path

# ensure package import paths work when executed from repo root
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from backend_expenses import models
from backend_expenses.database import engine

def main():
    print("Creating database tables (if they don't exist)...")
    models.Base.metadata.create_all(bind=engine)
    print("Done. Tables created/verified.")

if __name__ == "__main__":
    main()
