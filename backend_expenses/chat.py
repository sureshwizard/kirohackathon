# backend_expenses/chat.py
from fastapi import APIRouter, Request
from typing import Dict, Any, Optional
from datetime import datetime
import sqlite3

# Adjust import path if needed
from backend_ingest.parsers.intent import detect_item_month_query
from backend_expenses.database import get_conn

router = APIRouter(prefix="/api/v1", tags=["chat"])


def total_for_keyword_month(keyword: str, year: int, month: int) -> Dict[str, Any]:
    """
    Compute sum(total_amount) and count of transactions for a keyword in a given year-month.
    Uses substr(tx_datetime,1,7) = 'YYYY-MM' to handle mixed timestamp formats.
    Searches note, exp_type, source (case-insensitive).
    """
    ym = f"{year:04d}-{month:02d}"
    like = f"%{keyword.lower()}%"
    conn = get_conn()
    cur = conn.cursor()
    sql = """
    SELECT SUM(total_amount) AS total, COUNT(*) AS tx_count
    FROM expenses
    WHERE substr(coalesce(tx_datetime,''),1,7) = ?
      AND (
        lower(coalesce(note,'')) LIKE ?
        OR lower(coalesce(exp_type,'')) LIKE ?
        OR lower(coalesce(source,'')) LIKE ?
      )
    """
    cur.execute(sql, (ym, like, like, like))
    row = cur.fetchone()
    conn.close()
    total = float(row["total"]) if row and row["total"] is not None else 0.0
    tx_count = int(row["tx_count"]) if row and row["tx_count"] is not None else 0
    return {"keyword": keyword, "year": year, "month": month, "total": total, "tx_count": tx_count}


# Replace/point this to your existing chat/AI handling function.
# If you already have a function that handles generic prompts, import it here.
def handle_generic_chat_text(text: str, payload: Dict[str, Any]) -> str:
    """
    Minimal fallback: return month total for 'this month' style queries, otherwise echo.
    Replace this with your AI/chat logic.
    """
    # Example: if user asks "total this month" -> return sum of month
    s = text.lower()
    if "this month" in s or "total this month" in s:
        now = datetime.utcnow()
        ym = f"{now.year:04d}-{now.month:02d}"
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT SUM(total_amount) AS total FROM expenses WHERE substr(coalesce(tx_datetime,''),1,7)=?", (ym,))
        row = cur.fetchone()
        conn.close()
        total = float(row["total"]) if row and row["total"] is not None else 0.0
        return f"Your total spend this month is {total:.2f}."
    # default echo (replace with AI)
    return "Sorry — I couldn't detect a specific item. " \
           "Try asking: 'How much I spent on coffee this month?'"


@router.post("/chat")
async def chat_endpoint(req: Request):
    """
    Chat endpoint enhanced with item-month detection:
    - If message matches an item-month intent (eg. coffee this month), return item-specific total.
    - Otherwise, fall back to generic chat handler (AI or rule-based).
    Expects JSON payload with fields like { "message": "...", "text": "..." }.
    """
    payload = await req.json()
    # accept multiple possible fields for the user text
    text = payload.get("message") or payload.get("text") or ""
    if not text:
        return {"reply": "Sorry, I didn't receive any message."}

    # 1) Try to detect item-month intent
    detected = detect_item_month_query(text)
    if detected and detected.get("keyword"):
        keyword = detected["keyword"]
        year = detected.get("year", datetime.utcnow().year)
        month = detected.get("month", datetime.utcnow().month)

        # compute totals
        res = total_for_keyword_month(keyword, year, month)
        total = res["total"]
        tx_count = res["tx_count"]

        if tx_count == 0:
            reply = f"No expenses found for '{keyword}' in {year}-{month:02d}."
        else:
            reply = f"You spent {total:.2f} on '{keyword}' in {year}-{month:02d} across {tx_count} transaction(s)."

        return {"reply": reply, "data": res}

    # 2) Not an item query — fallback to existing chat/AI logic
    reply = handle_generic_chat_text(text, payload)
    return {"reply": reply}
