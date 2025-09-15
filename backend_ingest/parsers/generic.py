# backend_ingest/parsers/generic.py
from typing import List, Dict
from datetime import datetime

# expanded keywords set (include coffee/cafe)
GROCERY_KEYWORDS = {
    "rice", "wheat", "tomato", "onion", "oil", "sugar", "milk",
    "bread", "butter", "fruits", "vegetables"
}
ITEM_KEYWORDS = {
    "coffee", "cafe", "starbucks", "barista", "tea", "latte", "espresso"
}

DATE_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d/%b/%Y"]

def _parse_date(s: str):
    if not s:
        return None
    s = s.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    # fallback: try iso
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def parse(rows: List[Dict]) -> List[Dict]:
    parsed = []
    for r in rows:
        date_raw = (r.get("Date") or r.get("date") or r.get("Txn Date") or "").strip()
        tx_dt = _parse_date(date_raw)
        desc = (r.get("Description") or r.get("Desc") or r.get("note") or "").strip()
        amt_raw = r.get("Amount") or r.get("amount") or "0"
        try:
            # keep sign so refunds (-1200) remain negative
            amt = float(str(amt_raw).replace(",", "") or 0.0)
        except Exception:
            amt = 0.0

        # naive exp_type detection
        exp_type = "misc"
        low_desc = desc.lower()

        # If item keywords found, tag item-specific exp_type
        for k in ITEM_KEYWORDS:
            if k in low_desc:
                exp_type = "coffee" if k in {"coffee", "cafe", "starbucks"} else "misc"
                break

        # fallback grocery mapping
        if exp_type == "misc":
            for k in GROCERY_KEYWORDS:
                if k in low_desc:
                    exp_type = "groceries"
                    break

        parsed.append({
            "tx_datetime": tx_dt.isoformat() if tx_dt else None,
            "exp_type": exp_type,
            "total_amount": amt,
            "note": desc,
            "txn_id": r.get("TxnID") or r.get("RefNo") or ""
        })
    return parsed


# convenience wrapper used by app
def parse_rows(source: str, rows: List[Dict]) -> List[Dict]:
    # You might want to route different sources to different parsers
    return parse(rows)


def parse_text(source: str, text: str) -> List[Dict]:
    # stub for text parsing (OCR / invoice parsing). Keep simple for now.
    # This should return the same shape as parse_rows entries.
    return []
