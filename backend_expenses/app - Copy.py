# backend_expenses/app.py
import os
from datetime import datetime
from typing import Generator, Optional

import uvicorn
from fastapi import FastAPI, Body, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend_expenses.chat import router as chat_router
import re
from calendar import monthrange


# local imports
from . import models, crud, utils
from .database import SessionLocal, engine
from .models import Expense  # used in chat handler

# create DB tables if not exist
models.Base.metadata.create_all(bind=engine)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)

app = FastAPI(title="Monexa - Expenses API")
app.include_router(chat_router)
# CORS for frontend (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with ["http://localhost:3000"] in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
#------------------------------------------
# Replace or add this in backend_expenses/app.py

def parse_user_text(text: str, now: datetime = None):
    """
    Conservative parser: detects intent, term/category, numeric threshold,
    and returns a start_date/end_date for the query (YYYY-MM-DD).
    """
    if now is None:
        now = datetime.now()
    t = (text or "").lower().strip()

    # --- Intent detection (ordered, specific first) ---
    if any(k in t for k in ["top 5 merchants", "top merchants", "top 5", "top merchants i"]):
        intent = "top_merchants"
    elif any(k in t for k in ["category summary","by category","show categories","category"]):
        intent = "category_summary"
    elif any(k in t for k in ["above", "over", "greater than", "more than"]):
        intent = "large_txn"
    elif any(k in t for k in ["how much", "spent", "total", "sum", "what did i spend"]):
        intent = "sum_by_term"
    else:
        # fallback heuristics
        if re.search(r'\b(above|over|greater than)\b', t):
            intent = "large_txn"
        else:
            intent = "sum_by_term"

    # --- numeric threshold extraction (for large_txn) ---
    thr = None
    m = re.search(r'(?:above|over|greater than|>)\s*₹?\s*([0-9,]+(?:\.\d+)?)', t)
    if m:
        thr = float(m.group(1).replace(',', ''))
    else:
        # if bare number and intent indicates large_txn, use it
        m2 = re.search(r'\b([0-9]{3,}(?:\.\d+)?)\b', t)
        if m2 and intent == "large_txn":
            thr = float(m2.group(1).replace(',', ''))

    # --- term/category extraction: "on <term>" or "for <term>" (avoid stopwords) ---
    term = None
    m = re.search(r'\b(?:on|for|about)\s+([a-z0-9 &\-]+?)(?:\s|$|\?)', t)
    if m:
        candidate = m.group(1).strip()
        if candidate not in {"with","the","a","an","this","that","month","this month"}:
            term = candidate

    # fallback known categories
    if not term:
        for kw in ["coffee","tea","groceries","dining","shopping","transport","health"]:
            if kw in t:
                term = kw
                break

    # For top_merchants we do not treat any following word as term
    if intent == "top_merchants":
        term = None

    # --- date range detection (this/last month, YYYY-MM, or default this month) ---
    start_date = end_date = None
    if "this month" in t:
        y, mo = now.year, now.month
    elif "last month" in t:
        mo = now.month - 1 or 12
        y = now.year if now.month != 1 else now.year - 1
    else:
        m = re.search(r'(20\d{2})[-/](0[1-9]|1[0-2])', t)
        if m:
            y, mo = int(m.group(1)), int(m.group(2))
        else:
            m2 = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(20\d{2})', t)
            if m2:
                months = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
                mo = months[m2.group(1)[:3]]; y = int(m2.group(2))
            else:
                y, mo = now.year, now.month

    start_date = f"{y:04d}-{mo:02d}-01"
    end_date = f"{y:04d}-{mo:02d}-{monthrange(y,mo)[1]:02d}"

    return {"intent": intent, "term": term, "threshold": thr, "start_date": start_date, "end_date": end_date}




#--------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to Monexa Expenses API"}

# --- Expenses endpoints ---
@app.post("/expenses/")
def add_expense(exp: models.ExpenseCreate, db: Session = Depends(get_db)):
    return crud.create_expense(db, exp)

@app.get("/expenses/")
def list_expenses(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.get_expenses(db, skip=skip, limit=limit)

# --- Reports endpoints (use utils) ---
@app.get("/reports/monthly")
def report_monthly(year: int, month: int, db: Session = Depends(get_db)):
    return utils.get_monthly_report(db, year, month)

@app.get("/reports/compare")
def report_compare(y1: int, m1: int, y2: int, m2: int, db: Session = Depends(get_db)):
    return utils.compare_months(db, (y1, m1), (y2, m2))

# --- Chat route (safe: placed after get_db, no circular imports) ---

# Stopwords / time words we should not treat as keyword
STOPWORDS = {
    "this", "month", "today", "yesterday", "spent", "spend", "amount", "much", "how", "i", "on", "for", "in", "the",
    "my", "me", "a", "an", "is", "are", "of", "to"
}
TIME_PHRASES = {
    "this month", "this week", "today", "yesterday", "this year", "last month", "last week", "this quarter"
}

def _extract_keyword(text: str) -> Optional[str]:
    """
    Extract a candidate keyword/phrase from the user's question.
    Rules:
      - If user explicitly says "on <phrase>" or "for <phrase>", return that phrase (trimmed).
      - Ignore common time phrases (e.g. "this month") — return None in that case so caller sums whole period.
      - Otherwise, pick the first non-stopword token and return it (single word).
      - Return None if nothing sensible found.
    """
    if not text:
        return None

    low = text.lower()

    # If a time phrase is present, don't treat it as keyword
    for tp in TIME_PHRASES:
        if tp in low:
            # We still continue, because time phrase presence shouldn't block explicit "on/for" phrases
            # but if only time phrase exists (no entity), caller will get None later.
            pass

    # Prefer explicit phrasing: "on <phrase>" or "for <phrase>" (capture multi-word)
    m = re.search(r"(?:\b(?:on|for)\b)\s+([a-z0-9 _&\-\']+)", text, re.IGNORECASE)
    if m:
        candidate = m.group(1).strip().lower()
        # If candidate contains a time phrase, ignore it
        if any(tp in candidate for tp in TIME_PHRASES):
            return None
        # remove trailing time words from the candidate (e.g., "coffee this month")
        for tp in TIME_PHRASES:
            if tp in candidate:
                candidate = candidate.replace(tp, "").strip()
        # collapse whitespace
        candidate = " ".join(candidate.split())
        if candidate and all(tok not in STOPWORDS for tok in candidate.split()):
            return candidate

    # Another pattern: "spent on <phrase>" or "spent with <phrase>"
    m2 = re.search(r"spent(?:\s+(?:on|with|for))\s+([a-z0-9 _&\-\']+)", text, re.IGNORECASE)
    if m2:
        cand = m2.group(1).strip().lower()
        for tp in TIME_PHRASES:
            if tp in cand:
                cand = cand.replace(tp, "").strip()
        cand = " ".join(cand.split())
        if cand and all(tok not in STOPWORDS for tok in cand.split()):
            return cand

    # Fallback: scan tokens and return first non-stopword token that looks meaningful
    tokens = re.findall(r"[a-z0-9_&\-]+", low)
    for tok in tokens:
        if tok in TIME_PHRASES or tok in STOPWORDS:
            continue
        # avoid single-character tokens that are not meaningful
        if len(tok) <= 1:
            continue
        return tok

    return None


@app.post("/api/v1/chat")
def chat_endpoint(body: dict = Body(...), db: Session = Depends(get_db)):
    """
    Chat endpoint:
      - Accepts { message, text, use_ai }.
      - Handles specific intents (category summary, top merchants, large transactions, how much spent).
      - Returns actual data from DB (no synthetic values).
    """
    text_in = (body.get("message") or body.get("text") or "").strip()
    use_ai = bool(body.get("use_ai", False))

    if not text_in:
        return {"reply": "Please send a message in the request body (message or text field)."}

    lower = text_in.lower()

    # --- Intent: Category summary ---
    if "category summary" in lower or "show expenses by category" in lower or "category totals" in lower:
        now = datetime.now()
        report = utils.get_monthly_report(db, now.year, now.month)
        by_cat = report.get("by_category", [])
        if not by_cat:
            return {"reply": "No category data available for the current month."}
        lines = ["Category summary for this month:"]
        for r in by_cat:
            lines.append(f"- {r['exp_type']}: {r['total']:.2f} ({r['count']} txns)")
        return {"reply": "\n".join(lines)}

    # --- Intent: Top merchants ---
    if "top merchant" in lower or "top 5 merchants" in lower or "top merchants" in lower:
        now = datetime.now()
        ys = str(now.year); ms = f"{now.month:02d}"
        q = db.query(func.coalesce(Expense.note, "unknown").label("merchant"),
                     func.sum(Expense.total_amount).label("total"),
                     func.count(Expense.id).label("count")) \
              .filter(func.strftime("%Y", Expense.tx_datetime) == ys) \
              .filter(func.strftime("%m", Expense.tx_datetime) == ms) \
              .group_by(func.coalesce(Expense.note, "unknown")) \
              .order_by(func.abs(func.sum(Expense.total_amount)).desc()) \
              .limit(5)
        rows = q.all()
        if not rows:
            return {"reply": "No merchant data found for this month."}
        lines = ["Top merchants this month:"]
        for r in rows:
            merchant = r.merchant or "unknown"
            total = float(r.total or 0.0)
            cnt = int(r.count or 0)
            lines.append(f"- {merchant}: {total:.2f} ({cnt} txns)")
        return {"reply": "\n".join(lines)}

    # --- Intent: Large transactions ---
    if "large transaction" in lower or "large transactions" in lower or "above" in lower:
        # parse numeric threshold; default 1000
        m = re.search(r"(?:above|greater than|over)\s+₹?([0-9,]+)", lower)
        if m:
            thr = float(m.group(1).replace(",", ""))
        else:
            thr = 1000.0
        now = datetime.now()
        ys = str(now.year); ms = f"{now.month:02d}"
        q = db.query(Expense.tx_datetime, Expense.exp_type, Expense.total_amount, Expense.note) \
              .filter(func.strftime("%Y", Expense.tx_datetime) == ys) \
              .filter(func.strftime("%m", Expense.tx_datetime) == ms) \
              .filter(func.abs(Expense.total_amount) >= thr) \
              .order_by(func.abs(Expense.total_amount).desc()) \
              .limit(20)
        rows = q.all()
        if not rows:
            return {"reply": f"No transactions above {thr:.2f} found this month."}
        lines = [f"Transactions >= {thr:.2f} this month:"]
        for r in rows:
            dt = r.tx_datetime
            amt = float(r.total_amount or 0.0)
            note = (r.note or "").strip()
            lines.append(f"- {dt}: {amt:.2f} — {note}")
        return {"reply": "\n".join(lines)}

    # --- Intent: "how much ... spent" ---
    if "how much" in lower and "spent" in lower:
        now = datetime.now()
        year_s = str(now.year)
        month_s = f"{now.month:02d}"

        keyword = _extract_keyword(text_in)  # improved extractor
        q = db.query(func.sum(Expense.total_amount).label("total")) \
              .filter(func.strftime("%Y", Expense.tx_datetime) == year_s) \
              .filter(func.strftime("%m", Expense.tx_datetime) == month_s)

        if keyword:
            like = f"%{keyword}%"
            q = q.filter(
                func.lower(Expense.note).like(like) |
                func.lower(Expense.exp_type).like(like)
            )

        total_row = q.first()
        total = float(total_row.total or 0.0)
        # display positive magnitude for human-friendly phrasing if you prefer:
        # display_value = abs(total)
        if keyword:
            return {"reply": f"You spent {total:.2f} this month on '{keyword}'."}
        else:
            return {"reply": f"Your total spend this month is {total:.2f}."}

    # --- AI placeholder ---
    if use_ai:
        return {"reply": f"(AI not configured) I would answer: {text_in}"}

    # --- Fallback: echo ---
    return {"reply": f"You said: {text_in}"}

# Run with: python -m uvicorn backend_expenses.app:app --reload --port 8000
if __name__ == "__main__":
    uvicorn.run("backend_expenses.app:app", host="0.0.0.0", port=8000, reload=True)
