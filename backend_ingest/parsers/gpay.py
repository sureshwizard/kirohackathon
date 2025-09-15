from typing import List, Dict
from datetime import datetime

def parse_date(value: str):
    """Try multiple date formats to be more flexible."""
    if not value:
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None

def parse(rows: List[Dict]) -> List[Dict]:
    parsed = []
    for r in rows:
        # handle multiple possible column names
        dt_raw = r.get("Date") or r.get("tx_datetime") or ""
        dt = parse_date(dt_raw)

        amount_str = r.get("Amount") or r.get("total_amount") or "0"
        try:
            amount = float(amount_str)
        except Exception:
            amount = 0.0

        parsed.append({
            "tx_datetime": dt.isoformat() if dt else None,
            "exp_type": "gpay",
            "total_amount": amount,
            "note": r.get("Merchant") or r.get("Description") or r.get("note") or "",
            "txn_id": r.get("TxnID") or r.get("txn_id") or ""
        })
    return parsed
