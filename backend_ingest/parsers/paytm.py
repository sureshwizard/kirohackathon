from typing import List, Dict
from datetime import datetime

def parse_date(value: str):
    """Try multiple date formats (Paytm often uses dd/mm/yyyy)."""
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None

def parse(rows: List[Dict]) -> List[Dict]:
    parsed = []
    for r in rows:
        # Handle multiple possible date fields
        dt_raw = r.get("Date") or r.get("tx_datetime") or ""
        dt = parse_date(dt_raw)

        # Handle amount
        amount_str = r.get("Amount") or r.get("total_amount") or "0"
        try:
            amount = float(amount_str.replace(",", "").strip())
        except Exception:
            amount = 0.0

        parsed.append({
            "tx_datetime": dt.isoformat() if dt else None,
            "exp_type": "paytm",
            "total_amount": amount,
            "note": r.get("Narration") or r.get("note") or "",
            "txn_id": r.get("OrderID") or r.get("txn_id") or ""
        })
    return parsed
