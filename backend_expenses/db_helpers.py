# backend_expenses/db_helpers.py
import sqlite3
from .utils_datetime_amount import normalize_tx_datetime, normalize_amount

def insert_expense(conn: sqlite3.Connection, record: dict):
    tx = normalize_tx_datetime(record.get("tx_datetime"))
    amt = normalize_amount(record.get("total_amount"))
    exp_type = record.get("exp_type") or None
    note = record.get("note") or None
    source = record.get("source") or None
    txn_id = record.get("txn_id") or None

    sql = """
    INSERT INTO expenses (tx_datetime, exp_type, total_amount, note, source, txn_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, (tx, exp_type, amt, note, source, txn_id))
    conn.commit()
    return cur.lastrowid
