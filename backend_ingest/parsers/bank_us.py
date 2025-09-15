from typing import List, Dict
from datetime import datetime
import re

def parse_date(value: str):
    """Try several common date formats and return a datetime or None."""
    if not value:
        return None
    value = str(value).strip()
    formats = [
        "%m/%d/%Y",          # 09/14/2025 (US style)
        "%d-%m-%Y",          # 14-09-2025
        "%d/%m/%Y",          # 14/09/2025
        "%Y-%m-%d",          # 2025-09-14
        "%Y-%m-%dT%H:%M:%S", # 2025-09-14T10:30:12
        "%d-%b-%Y",          # 14-Sep-2025
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
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
    s = re.sub(r"[₹$€,]", "", s)  # remove currency symbols
    if re.match(r"^\(.*\)$", s):  # handle negatives like (1200.00)
        s = "-" + s.strip("()")
    s = s.replace(" ", "").replace(",", "")
    try:
        return float(s)
    except Exception:
        m = re.search(r"-?[\d]+(?:\.[\d]+)?", s)
        return float(m.group(0)) if m else 0.0

def parse(bank: str, rows: List[Dict]) -> List[Dict]:
    """
    Robust parser for US-style bank/credit-card CSVs.
    Handles flexible headers and multiple date/amount formats.
    """
    parsed = []
    for r in rows:
        # Date
        dt_raw = (
            r.get("Date")
            or r.get("Transaction Date")
            or r.get("tx_datetime")
            or ""
        )
        dt = parse_date(dt_raw)

        # Amount
        amount_raw = (
            r.get("Amount")
            or r.get("total_amount")
            or r.get("Value")
            or "0"
        )
        amount = parse_amount(amount_raw)

        # Note / description
        note = (
            r.get("Description")
            or r.get("Details")
            or r.get("Narration")
            or r.get("note")
            or ""
        )

        # Transaction ID
        txn_id = (
            r.get("TransactionID")
            or r.get("TxnID")
            or r.get("OrderID")
            or r.get("RefNo")
            or r.get("txn_id")
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
