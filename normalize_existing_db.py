# normalize_existing_db.py
import sqlite3
from backend_expenses.utils_datetime_amount import normalize_tx_datetime, normalize_amount

DB = r"C:\business\21-projects\monexa\data\Finance.db"

def normalize_db(db_path=DB):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, tx_datetime, total_amount FROM expenses")
    rows = cur.fetchall()
    updates = []
    for _id, raw_dt, raw_amt in rows:
        new_dt = normalize_tx_datetime(raw_dt)
        new_amt = normalize_amount(raw_amt)
        # decide whether to update (convert None->NULL, string->normalized)
        if (new_dt is not None and new_dt != raw_dt) or (new_amt is not None and str(new_amt) != ("" if raw_amt is None else str(raw_amt))):
            updates.append((_id, new_dt, new_amt))
    print(f"Found {len(updates)} rows to update")
    for _id, new_dt, new_amt in updates:
        cur.execute("UPDATE expenses SET tx_datetime = ?, total_amount = ? WHERE id = ?", (new_dt, new_amt, _id))
    conn.commit()
    conn.close()
    print("Normalization complete.")

if __name__ == "__main__":
    normalize_db()
