from typing import List, Dict, Any
from datetime import datetime
from difflib import SequenceMatcher
from backend_expenses.database import get_conn

def normalize(s: str) -> str:
    return (s or "").lower().strip()

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def preview(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, tx_datetime, total_amount, note, source, txn_id FROM expenses ORDER BY tx_datetime DESC LIMIT 500")
    existing = [dict(r) for r in cur.fetchall()]

    results = []
    for r in rows:
        candidates = []
        for ex in existing:
            amt_close = abs(float(r.get("total_amount", 0)) - float(ex["total_amount"])) < 1.0
            sim = similarity(r.get("note", ""), ex.get("note", ""))
            if amt_close and sim > 0.6:
                candidates.append({"existing": ex, "sim": sim})
        results.append({"incoming": r, "candidates": candidates})
    conn.close()
    return {"results": results}

def find_in_db() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, tx_datetime, total_amount, note, source, txn_id FROM expenses")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    # naive: return total count
    return {"scanned": len(rows)}
