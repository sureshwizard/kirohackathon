#!/usr/bin/env python3
"""
db_browser.py

Quick diagnostics for finance.db:
- prints file path
- prints counts: expenses, expense_items
- prints top 8 categories by total amount (descending)
- prints last 5 expense rows (id, date, type, amount, note)

Usage:
    python backend_expenses/db_browser.py
"""

import sys
from pathlib import Path
import sqlite3
import json

# ensure package import paths work when executed from repo root
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from backend_expenses.database import FINANCE_DB, get_conn

def row_to_dict(row):
    return {k: row[k] for k in row.keys()}

def main():
    print("Monexa DB browser")
    print("DB path:", FINANCE_DB)
    conn = get_conn()
    cur = conn.cursor()

    try:
        # counts
        cur.execute("SELECT COUNT(*) as c FROM sqlite_master WHERE type='table' AND name='expenses'")
        has_expenses_table = cur.fetchone()["c"] > 0

        if not has_expenses_table:
            print("No 'expenses' table found. Run bootstrap_db.py to create schema.")
            return

        cur.execute("SELECT COUNT(*) as cnt FROM expenses")
        total_exp = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) as cnt FROM expense_items")
        total_items = cur.fetchone()["cnt"]

        print(f"Total expenses: {total_exp}")
        print(f"Total expense items: {total_items}")

        # top categories (by total amount)
        cur.execute("""
            SELECT exp_type, SUM(total_amount) as total, COUNT(*) as cnt
            FROM expenses
            GROUP BY exp_type
            ORDER BY total DESC
            LIMIT 8
        """)
        top_cats = [row_to_dict(r) for r in cur.fetchall()]
        print("\nTop categories (by total amount):")
        if top_cats:
            for r in top_cats:
                print(f" - {r['exp_type']}: total={r['total']} count={r['cnt']}")
        else:
            print(" (no data)")

        # last 5 expenses
        cur.execute("""
            SELECT id, tx_datetime, exp_type, total_amount, note
            FROM expenses
            ORDER BY tx_datetime DESC
            LIMIT 5
        """)
        last5 = [row_to_dict(r) for r in cur.fetchall()]
        print("\nLast 5 expenses:")
        if last5:
            for r in last5:
                print(f" - id={r['id']} date={r['tx_datetime']} type={r['exp_type']} amount={r['total_amount']} note={r.get('note')}")
        else:
            print(" (no expenses)")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
