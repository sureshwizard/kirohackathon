# backend_expenses/app.py
import os
import re
from datetime import datetime
from typing import Generator, Optional

import uvicorn
from fastapi import FastAPI, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from calendar import monthrange
from openai import OpenAI
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
# local imports
from . import models, crud, utils
from .database import SessionLocal, engine
from .models import Expense  # used in chat handler

# --- Setup DB ---
models.Base.metadata.create_all(bind=engine)

# --- OpenAI ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# --- FastAPI ---
app = FastAPI(title="Monexa - Expenses API")
#-----logger --------

logger = logging.getLogger("uvicorn.error")
# CORS for frontend (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in prod
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

# -------------------------------------------------------
# Expenses + Reports (unchanged so frontend works fine)
# -------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to Monexa Expenses API"}

@app.post("/expenses/")
def add_expense(exp: models.ExpenseCreate, db: Session = Depends(get_db)):
    return crud.create_expense(db, exp)

@app.get("/expenses/")
def list_expenses(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.get_expenses(db, skip=skip, limit=limit)

@app.get("/reports/monthly")
def report_monthly(year: int, month: int, db: Session = Depends(get_db)):
    return utils.get_monthly_report(db, year, month)

@app.get("/reports/compare")
def report_compare(y1: int, m1: int, y2: int, m2: int, db: Session = Depends(get_db)):
    return utils.compare_months(db, (y1, m1), (y2, m2))

# -------------------------------------------------------
# Chat
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # log full traceback
    logger.exception("Unhandled exception while handling request %s %s: %s", request.method, request.url, exc)
    return JSONResponse(status_code=500, content={"detail": "Server error", "error": str(exc)})
# -------------------------------------------------------

STOPWORDS = {"this", "month", "today", "yesterday", "spent", "spend", "amount",
             "much", "how", "i", "on", "for", "in", "the", "my", "me", "a", "an"}
TIME_PHRASES = {"this month", "last month", "today", "yesterday"}

def _extract_keyword(text: str) -> Optional[str]:
    """
    Extract a candidate keyword/phrase from the user's question.
    - Prefer "on <phrase>" or "for <phrase>"
    - Strip trailing time phrases like "this month", "this week"
    - Return single cleaned phrase (lowercased) or None
    """
    if not text:
        return None
    low = text.lower().strip()

    TIME_PHRASES = ["this month", "last month", "this week", "today", "yesterday", "this year"]
    STOPWORDS = {"this", "month", "today", "yesterday", "spent", "spend", "amount",
                 "much", "how", "i", "on", "for", "in", "the", "my", "me", "a", "an"}

    # Prefer explicit phrasing: "on <phrase>" or "for <phrase>"
    m = re.search(r"(?:\bon\b|\bfor\b)\s+([a-z0-9 _&\-\']+)", low, re.IGNORECASE)
    if m:
        cand = m.group(1).strip()
        # remove trailing time phrases if present
        for tp in TIME_PHRASES:
            if cand.endswith(tp):
                cand = cand[: -len(tp)].strip()
        cand = " ".join(cand.split())
        # final checks
        if cand and not all(tok in STOPWORDS for tok in cand.split()):
            return cand

    # Pattern: "spent on <phrase>" or "spent with <phrase>"
    m2 = re.search(r"spent(?:\s+(?:on|with|for))\s+([a-z0-9 _&\-\']+)", low, re.IGNORECASE)
    if m2:
        cand = m2.group(1).strip()
        for tp in TIME_PHRASES:
            if tp in cand:
                cand = cand.replace(tp, "").strip()
        cand = " ".join(cand.split())
        if cand and not all(tok in STOPWORDS for tok in cand.split()):
            return cand

    # Fallback: first non-stopword token that is meaningful
    tokens = re.findall(r"[a-z0-9_&\-]+", low)
    for tok in tokens:
        if tok in STOPWORDS:
            continue
        if len(tok) <= 1:
            continue
        return tok

    return None
def _format_monthly_context(db: Session, year: int, month: int) -> str:
    rep = utils.get_monthly_report(db, year, month)
    by_cat = rep.get("by_category", []) if rep else []
    if not by_cat:
        return "No recorded expenses for this month."
    parts = []
    for r in by_cat:
        parts.append(f"{r.get('exp_type','unknown')}: {float(r.get('total') or 0.0):.2f} ({int(r.get('count') or 0)} txns)")
    return " | ".join(parts)

def ask_openai(user_question: str, db: Session, max_tokens: int = 300) -> str:
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY not set on server")
    now = datetime.now()
    ctx = _format_monthly_context(db, now.year, now.month)
    system_msg = (
        "You are Monexa, a concise personal finance assistant. "
        "Use the provided context (monthly totals by category) to answer user questions precisely. "
        "If the answer depends on data not in the context, say you don't have that info and suggest how to retrieve it."
    )
    user_msg = f"Context: {ctx}\n\nUser question: {user_question}"
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # change if you need another model
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return resp["choices"][0]["message"]["content"].strip()

@app.post("/api/v1/chat")
def chat_endpoint(body: dict = Body(...), db: Session = Depends(get_db)):
    try:
        text_in = (body.get("message") or body.get("text") or "").strip()
        use_ai = bool(body.get("use_ai", False))

        if not text_in:
            return {"reply": "Please send a message in the request body (message or text field)."}

        # If user requested AI, force it and return AI reply (ask_openai should raise RuntimeError if key missing)
        if use_ai:
            try:
                ai_reply = ask_openai(text_in, db)
                return {"reply": ai_reply, "source": "ai"}
            except RuntimeError as rte:
                # runtime error from ask_openai (e.g., API key missing)
                return {"reply": f"AI not configured on server: {str(rte)}", "source": "ai_error"}
            except Exception as err:
                logger.exception("OpenAI call failed: %s", err)
                return {"reply": "AI service error — please try again later.", "source": "ai_error"}

        lower = text_in.lower()

        # Category summary
        if "category summary" in lower or "show expenses by category" in lower or "category totals" in lower:
            now = datetime.now()
            report = utils.get_monthly_report(db, now.year, now.month)
            by_cat = report.get("by_category", [])
            if not by_cat:
                return {"reply": "No category data available for the current month.", "source": "db"}
            lines = ["Category summary for this month:"]
            for r in by_cat:
                lines.append(f"- {r['exp_type']}: {r['total']:.2f} ({r['count']} txns)")
            return {"reply": "\n".join(lines), "source": "db"}

        # Top merchants
        if "top merchant" in lower or "top 5 merchants" in lower or "top merchants" in lower:
            now = datetime.now()
            ys = str(now.year); ms = f"{now.month:02d}"
            q = db.query(
                    func.coalesce(Expense.note, "unknown").label("merchant"),
                    func.sum(Expense.total_amount).label("total"),
                    func.count(Expense.id).label("count")
                ) \
                .filter(func.strftime("%Y", Expense.tx_datetime) == ys) \
                .filter(func.strftime("%m", Expense.tx_datetime) == ms) \
                .group_by(func.coalesce(Expense.note, "unknown")) \
                .order_by(func.abs(func.sum(Expense.total_amount)).desc()) \
                .limit(5)
            rows = q.all()
            if not rows:
                return {"reply": "No merchant data found for this month.", "source": "db"}
            lines = ["Top merchants this month:"]
            for r in rows:
                lines.append(f"- {r.merchant or 'unknown'}: {float(r.total or 0):.2f} ({r.count} txns)")
            return {"reply": "\n".join(lines), "source": "db"}

        # Large transactions
        if "large transaction" in lower or "large transactions" in lower or "above" in lower:
            m = re.search(r"(?:above|over|greater than)\s+₹?([0-9,]+(?:\.\d+)?)", lower)
            thr = float(m.group(1).replace(",", "")) if m else 1000.0
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
                return {"reply": f"No transactions above {thr:.2f} found this month.", "source": "db"}
            lines = [f"Transactions ≥ {thr:.2f} this month:"]
            for r in rows:
                dt = r.tx_datetime
                amt = float(r.total_amount or 0.0)
                note = (r.note or "").strip()
                lines.append(f"- {dt}: {amt:.2f} — {note}")
            return {"reply": "\n".join(lines), "source": "db"}

        # "how much ... spent"  — use parentheses to group correctly
        if (re.search(r"\b(how much|what(?:'s| is) my total|how much did i spend|total (?:spend|spent))\b", lower)
                and ("spent" in lower or "spend" in lower)):
            now = datetime.now()
            ys = str(now.year); ms = f"{now.month:02d}"
            keyword = _extract_keyword(text_in)
            q = db.query(func.sum(Expense.total_amount).label("total")) \
                  .filter(func.strftime("%Y", Expense.tx_datetime) == ys) \
                  .filter(func.strftime("%m", Expense.tx_datetime) == ms)
            if keyword:
                like = f"%{keyword}%"
                q = q.filter(func.lower(Expense.note).like(like) | func.lower(Expense.exp_type).like(like))
            total_row = q.first()
            total = float(total_row.total or 0.0)
            if keyword:
                return {"reply": f"You spent {total:.2f} this month on '{keyword}'.", "source": "db"}
            else:
                return {"reply": f"Your total spend this month is {total:.2f}.", "source": "db"}

        # fallback
        return {"reply": f"You said: {text_in}", "source": "db"}

    except Exception as exc:
        logger.exception("Error in chat_endpoint: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "chat handler error", "error": str(exc)})
# -------------------------------------------------------
# Run
# -------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("backend_expenses.app:app", host="0.0.0.0", port=8000, reload=True)
