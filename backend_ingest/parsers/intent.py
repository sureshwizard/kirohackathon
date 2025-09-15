# backend_ingest/parsers/intent.py
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any, Set, Iterable
import sqlite3
import string

# adjust import path to your DB helper
from backend_expenses.database import get_conn

# Static seed keywords you want always present
STATIC_SEED = {"coffee", "cafe", "starbuck", "starbucks", "tea", "latte", "espresso", "chai", "beer", "wine"}

# Minimal stopwords / tokens to ignore when building dynamic keywords
_STOPWORDS = {
    "the", "and", "for", "with", "from", "to", "on", "in", "at", "by", "of", "a", "an", "txn", "gpay", "upi", "pay",
    "paytm", "google", "amazon", "order", "online", "cash", "debit", "credit"
}

# caching dynamic keywords for performance
_KEYWORD_CACHE: Dict[str, Any] = {
    "keywords": set(STATIC_SEED),
    "updated_at": 0.0,
    "ttl": 300  # seconds; refresh every 5 minutes (tune as needed)
}

# tokenization helpers
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")  # grab alphanumeric words

def _tokenize(text: str) -> Iterable[str]:
    if not text:
        return ()
    # extract alphanumeric tokens only, lowercase
    return (tok.lower() for tok in _TOKEN_RE.findall(text or ""))

def _is_valid_token(tok: str) -> bool:
    if not tok:
        return False
    if tok in _STOPWORDS:
        return False
    if len(tok) < 3:  # ignore tiny tokens like 'is','to','on' — tune if needed
        return False
    # ignore pure-numeric tokens (txn ids, amounts)
    if tok.isdigit():
        return False
    return True

def build_dynamic_keywords_from_db(conn: sqlite3.Connection) -> Set[str]:
    """
    Query distinct note, source, exp_type from `expenses` and extract candidate tokens.
    Returns a set of lowercased words merged with STATIC_SEED.
    """
    kws = set(STATIC_SEED)
    cur = conn.cursor()

    # Query distinct values for the three columns; use COALESCE to avoid NULL
    try:
        # Use a union of distinct columns
        cur.execute("""
            SELECT DISTINCT note as val FROM expenses
            UNION
            SELECT DISTINCT source FROM expenses
            UNION
            SELECT DISTINCT exp_type FROM expenses
        """)
    except Exception:
        # Fallback to three separate queries if UNION unsupported for some reason
        try:
            cur.execute("SELECT DISTINCT note FROM expenses")
            rows = cur.fetchall()
        except Exception:
            rows = []
        # process rows below
        values = [r[0] for r in rows if r and r[0]]
    else:
        rows = cur.fetchall()
        values = [r[0] for r in rows if r and r[0]]

    for v in values:
        # strip punctuation at ends, then tokenize
        # tokenization already pulls alphanumerics only
        for tok in _tokenize(str(v)):
            if _is_valid_token(tok):
                kws.add(tok)

    return kws

def _refresh_keyword_cache_if_needed() -> Set[str]:
    now = time.time()
    ttl = _KEYWORD_CACHE.get("ttl", 300)
    if (now - _KEYWORD_CACHE.get("updated_at", 0)) < ttl and _KEYWORD_CACHE.get("keywords"):
        return _KEYWORD_CACHE["keywords"]

    # refresh from DB
    try:
        conn = get_conn()
        kws = build_dynamic_keywords_from_db(conn)
        conn.close()
    except Exception:
        # if DB read fails, fall back to static seed
        kws = set(STATIC_SEED)

    _KEYWORD_CACHE["keywords"] = kws
    _KEYWORD_CACHE["updated_at"] = now
    return kws

# high-level detection function
def detect_item_month_query(text: str) -> Optional[Dict[str, Any]]:
    """
    Detect queries like "How much I spent on coffee this month?"
    Returns {"keyword": "coffee", "year": 2025, "month": 9} or None.
    Uses dynamic keywords from DB + static seed.
    """
    if not text or not text.strip():
        return None
    s = text.strip().lower()

    # get dynamic keywords (cached)
    keywords = _refresh_keyword_cache_if_needed()

    # quick pre-check: must contain "how much" or similar intent words
    if not re.search(r"\bhow much\b|\bwhat did i\b|\bspent\b|\bspend\b|\btotal\b", s):
        # still allow short forms like "coffee this month"
        if not re.search(r"\bthis month\b", s) and not re.search(r"\blast month\b", s):
            return None

    # attempt patterns in order of specificity
    now = datetime.utcnow()
    default_year = now.year
    default_month = now.month

    # pattern 1: explicit "this month"
    m = re.search(r"(?:how much(?: did i)?(?: i)?(?: spent|spent on|spent for|on|did i spend)?).*?(?:on|for)?\s+([a-z0-9\s]+?)\s+(?:this month)\b", s)
    if m:
        candidate_phrase = m.group(1).strip()
        # find any known keyword in the candidate phrase (longest-first)
        for tok in sorted(candidate_phrase.split(), key=len, reverse=True):
            if tok in keywords:
                return {"keyword": tok, "year": default_year, "month": default_month}
        # fallback: choose first token if it looks valid
        tok = candidate_phrase.split()[0]
        return {"keyword": tok, "year": default_year, "month": default_month}

    # pattern 2: simpler "how much on coffee" or "how much did i spend on tea"
    m2 = re.search(r"(?:how much|how much did i|what did i)\b.*(?:on|for)\s+([a-z0-9\s]+?)(?:\s+(?:this month|in|on|at|last month)\b.*)?$", s)
    if m2:
        candidate = m2.group(1).strip().split()[0]
        if candidate in keywords:
            return {"keyword": candidate, "year": default_year, "month": default_month}
        # try to find any keyword substring
        for k in keywords:
            if k in candidate:
                return {"keyword": k, "year": default_year, "month": default_month}
        return {"keyword": candidate, "year": default_year, "month": default_month}

    # pattern 3: "coffee this month" short form
    m3 = re.search(r"\b([a-z0-9]+)\s+this month\b", s)
    if m3:
        tok = m3.group(1)
        if tok in keywords:
            return {"keyword": tok, "year": default_year, "month": default_month}
        # allow token even if not in keyword list (best-effort)
        return {"keyword": tok, "year": default_year, "month": default_month}

    # pattern 4: last month / explicit month-year
    # "how much on coffee in sep 2025"
    m4 = re.search(r"(?:on|for|in)\s+([a-z]+)\s+(\d{4})", s)
    if m4:
        mon_name = m4.group(1)
        year = int(m4.group(2))
        try:
            dt = datetime.strptime(mon_name[:3], "%b")
            mnum = dt.month
        except Exception:
            try:
                dt = datetime.strptime(mon_name, "%B")
                mnum = dt.month
            except Exception:
                mnum = default_month
        # find keyword from text
        for k in keywords:
            if k in s:
                return {"keyword": k, "year": year, "month": mnum}
        return {"keyword": None, "year": year, "month": mnum}

    # pattern 5: last month
    if re.search(r"\blast month\b", s):
        # choose keyword from text if present
        for k in keywords:
            if k in s:
                # compute last month
                y = default_year
                mnum = default_month - 1
                if mnum == 0:
                    mnum = 12
                    y -= 1
                return {"keyword": k, "year": y, "month": mnum}

    return None
