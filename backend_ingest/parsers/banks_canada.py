# robust parser for bank-like CSVs
from typing import List, Dict
from datetime import datetime
import re

def parse_date(value: str):
    """Try several common date formats and return a datetime or None."""
    if not value:
        return None
    value = str(value).strip()
    formats = [
        "%Y-%m-%dT%H:%M:%S",  # 2025-09-14T10:30:12
        "%Y-%m-%d",           # 2025-09-14
        "%d-%m-%Y",           # 14-09-2025
        "%d/%m/%Y",           # 14/09/2025
        "%d-%b-%Y",           # 14-Sep-2025
        "%Y/%m/%d",           # 2025/09/14
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    # last resort: try fromisoformat
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None

def parse_amount(value: str):
    """Normalize amount strings to float. Strip commas, currency symbols, parentheses."""
    if value is None:
        return 0.0
    s = str(value).strip()
    if s == "":
        return 0.0
    # remove common currency symbols and separators
    s = re.sub(r"[₹$€,]", "", s)
    # handle parenthesis negative amounts like (1,200.00)
    if re.match(r"^\(.*\)$", s):
        s = "-" + s.strip("()")
    s = s.replace(" ", "")
    try:
        return float(s)
    except Exception:
        # fallback: extract numeric portion
        m = re.search(r"-?[\d]+(?:\.[\d]+)?", s)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return 0.0
        return 0.0

def parse(bank: str, rows: List[Dict]) -> List[Dict]:
    """
    Generic robust parser for bank-like CSVs.
    - bank: string to use as exp_type
    - rows: list of dicts from csv.DictReader
    Returns list of dicts with keys: tx_datetime (ISO string or None),
    exp_type, total_amount (float), note (str), txn_id (str)
    """
    parsed = []
    for r in rows:
        # date field - allow multiple header names
        dt_raw = (
            r.get("Date")
            or r.get("Txn Date")
            or r.get("Transaction Date")
            or r.get("tx_datetime")
            or r.get("timestamp")
            or ""
        )
        dt = parse_date(dt_raw)

        # amount field - allow multiple header names
        amount_raw = (
            r.get("Amount")
            or r.get("Amt")
            or r.get("total_amount")
            or r.get("Value")
            or "0"
        )
        amount = parse_amount(amount_raw)

        # note/description
        note = (
            r.get("Details")
            or r.get("Description")
            or r.get("Narration")
            or r.get("note")
            or r.get("Remarks")
            or ""
        )

        # txn id / reference
        txn_id = (
            r.get("TxnID")
            or r.get("Txn Id")
            or r.get("OrderID")
            or r.get("RefNo")
            or r.get("Ref")
            or r.get("txn_id")
            or r.get("transaction_id")
            or ""
        )

        parsed.append({
            "tx_datetime": dt.isoformat() if dt else None,
            "exp_type": bank,
            "total_amount": amount,
            "note": note,
            "txn_id": txn_id
        })
    return parsed
