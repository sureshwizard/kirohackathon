# backend_expenses/utils_datetime_amount.py
from datetime import datetime
import re

CURRENCY_RE = re.compile(r'[^\d.\-]+')  # remove anything that's not digit, dot, minus

def normalize_amount(raw_amount):
    if raw_amount is None:
        return None
    if isinstance(raw_amount, (int, float)):
        return float(raw_amount)
    s = str(raw_amount).strip()
    if s == '':
        return None
    cleaned = CURRENCY_RE.sub('', s)
    if cleaned == '':
        return None
    try:
        return float(cleaned)
    except ValueError:
        m = re.search(r'-?\d+(\.\d+)?', cleaned)
        return float(m.group(0)) if m else None

def normalize_tx_datetime(raw_dt):
    if raw_dt is None:
        return None
    s = str(raw_dt).strip()
    if s == '':
        return None
    s = s.replace('T', ' ')
    if '.' in s:
        s = s.split('.', 1)[0]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None
