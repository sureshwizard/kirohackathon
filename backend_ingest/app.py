# backend_ingest/app.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import csv
import io
from datetime import datetime

from . import parsers, dedupe
from backend_expenses.database import get_conn  # reuse DB connection

app = FastAPI(title="Monexa - Ingest Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to Ingest Data !!!!"}


@app.post("/preview_csv")
async def preview_csv(
    source: str = Form(...),
    file: UploadFile = File(...)
):
    """Parse CSV file without inserting into DB."""
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        parsed = parsers.parse_rows(source, rows)
        return {"source": source, "parsed": parsed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/upload_csv")
async def upload_csv(
    source: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Parse CSV rows via parsers.parse_rows(source, rows) and insert into DB.
    Also inserts any parsed 'items' into 'expense_items' table with expense_id FK.
    """
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        parsed = parsers.parse_rows(source, rows)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    conn = get_conn()  # your helper returning sqlite3.Connection
    cur = conn.cursor()
    imported = 0

    try:
        for r in parsed:
            # Ensure required fields exist (defensive)
            tx_dt = r.get("tx_datetime")
            exp_type = r.get("exp_type") or "misc"
            total_amount = r.get("total_amount") or 0.0
            note = r.get("note") or ""
            txn_id = r.get("txn_id") or None

            # Insert into expenses
            cur.execute(
                "INSERT INTO expenses (tx_datetime, exp_type, total_amount, note, source, txn_id) VALUES (?, ?, ?, ?, ?, ?)",
                (tx_dt, exp_type, total_amount, note, source, txn_id)
            )
            expense_id = cur.lastrowid
            imported += 1

            # Insert any line-items (optional)
            for it in r.get("items", []):
                try:
                    qty = float(it.get("quantity") or 0.0)
                except Exception:
                    qty = 0.0
                try:
                    amt = float(it.get("amount") or 0.0)
                except Exception:
                    amt = 0.0

                cur.execute(
                    "INSERT INTO expense_items (expense_id, quantity, amount) VALUES (?, ?, ?)",
                    (expense_id, qty, amt)
                )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")
    finally:
        conn.close()

    return {"imported": imported, "source": source}


@app.post("/upload_text")
async def upload_text(
    source: str = Form(...),
    text: str = Form(...)
):
    """Parse text bills/invoices and insert into DB."""
    parsed = parsers.parse_text(source, text)

    conn = get_conn()
    cur = conn.cursor()
    imported = 0
    try:
        for r in parsed:
            cur.execute(
                "INSERT INTO expenses (tx_datetime, exp_type, total_amount, note, source, txn_id) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    r.get("tx_datetime"),
                    r.get("exp_type"),
                    r.get("total_amount"),
                    r.get("note"),
                    source,
                    r.get("txn_id"),
                ),
            )
            imported += 1
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")
    finally:
        conn.close()
    return {"imported": imported}


# --- Dedupe endpoints (reuse dedupe.py) ---
@app.post("/dedupe_preview")
def dedupe_preview(rows: List[Dict[str, Any]]):
    return dedupe.preview(rows)


@app.get("/find_duplicates")
def find_duplicates():
    # return a list/dict from dedupe.find_in_db()
    return dedupe.find_in_db()


# --- Example quick query: amount for a keyword for a month ---
@app.post("/query_amount")
def query_amount(payload: Dict[str, Any] = Body(...)):
    """
    Example request JSON:
    {
      "keyword": "coffee",
      "year": 2025,
      "month": 9
    }
    Returns sum(total_amount) for expenses whose note or exp_type or source matches keyword.
    """
    keyword = str(payload.get("keyword", "")).strip().lower()
    year = int(payload.get("year", datetime.utcnow().year))
    month = int(payload.get("month", datetime.utcnow().month))

    conn = get_conn()
    cur = conn.cursor()

    # filter by year/month on tx_datetime (stored as ISO string)
    start = f"{year:04d}-{month:02d}-01T00:00:00"
    # naive end: next month first day (works for SQL string compare)
    if month == 12:
        nxt_year, nxt_month = year + 1, 1
    else:
        nxt_year, nxt_month = year, month + 1
    end = f"{nxt_year:04d}-{nxt_month:02d}-01T00:00:00"

    # search in note or exp_type or source
    q = """
    SELECT SUM(total_amount) as total, COUNT(*) as tx_count
    FROM expenses
    WHERE tx_datetime >= ? AND tx_datetime < ?
      AND (
          lower(note) LIKE ?
          OR lower(exp_type) LIKE ?
          OR lower(source) LIKE ?
      )
    """
    like = f"%{keyword}%"
    cur.execute(q, (start, end, like, like, like))
    row = cur.fetchone()
    conn.close()
    total = row["total"] if row and row["total"] is not None else 0.0
    tx_count = row["tx_count"] if row else 0
    return {"keyword": keyword, "year": year, "month": month, "total": float(total), "tx_count": tx_count}
