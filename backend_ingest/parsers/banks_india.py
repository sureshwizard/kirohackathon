# backend_ingest/parsers/bank.py
from typing import List, Dict
from datetime import datetime
import re

def parse_date(value: str):
    """Try several common date formats and return a datetime or None."""
    if not value:
        return None
    value = value.strip()
    formats = [
        "%d-%m-%Y",        # 14-09-2025
        "%d/%m/%Y",        # 14/09/2025
        "%Y-%m-%d",        # 2025-09-14
        "%Y-%m-%dT%H:%M:%S",  # 2025-09-14T10:30:12
        "%d-%b-%Y",        # 14-Sep-2025
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    # last resort: try to parse simple numeric timestamp or loose iso
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
    # remove common currency symbols and spaces
    s = re.sub(r"[₹$€,]", "", s)
    # handle values in parentheses as negative (e.g. (1,200.00))
    if re.match(r"^\(.*\)$", s):
        s = "-" + s.strip("()")
    # remove any remaining spaces
    s = s.replace(" ", "")
    try:
        return float(s)
    except Exception:
        # fallback: extract digits and dot
        m = re.search(r"-?[\d]+(?:\.[\d]+)?", s)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return 0.0
        return 0.0

def parse(bank: str, rows: List[Dict]) -> List[Dict]:
    """
    Robust bank CSV parser.
    Accepts multiple header names:
      - Txn Date, Transaction Date, Date, tx_datetime
      - Amount, Amt, total_amount
      - Description, Narration, note
      - RefNo, Ref, txn_id, TransactionRef
    Returns a list of dicts with keys:
      tx_datetime (ISO string or None), exp_type (bank param), total_amount (float),
      note (str), txn_id (str)
    """
    parsed = []
    for r in rows:
        # possible date fields
        dt_raw = (
            r.get("Txn Date")
            or r.get("Transaction Date")
            or r.get("Date")
            or r.get("tx_datetime")
            or r.get("timestamp")
            or ""
        )
        dt = parse_date(dt_raw)

        # possible amount fields
        amount_raw = (
            r.get("Amount")
            or r.get("Amt")
            or r.get("total_amount")
            or r.get("Credit")  # sometimes credit/debit separated
            or r.get("Debit")
            or "0"
        )
        amount = parse_amount(amount_raw)

        # note / description
        note = (
            r.get("Description")
            or r.get("Narration")
            or r.get("note")
            or r.get("Remarks")
            or ""
        )

        # txn id / reference
        txn_id = (
            r.get("RefNo")
            or r.get("Ref")
            or r.get("txn_id")
            or r.get("TransactionRef")
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
