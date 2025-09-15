# backend_expenses/utils.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import Expense
from datetime import datetime
from typing import Tuple, Dict, Any, List

def _fetch_by_category(db: Session, year: int, month: int) -> List[Dict[str, Any]]:
    """Return list of { exp_type, total, count } for the given year/month, sorted by abs(total)."""
    year_s = str(year)
    month_s = f"{month:02d}"

    q = (
        db.query(
            func.coalesce(Expense.exp_type, "misc").label("exp_type"),
            func.sum(Expense.total_amount).label("total"),
            func.count(Expense.id).label("count"),
        )
        .filter(func.strftime("%Y", Expense.tx_datetime) == year_s)
        .filter(func.strftime("%m", Expense.tx_datetime) == month_s)
        .group_by(func.coalesce(Expense.exp_type, "misc"))
    )

    rows = q.all()
    result = []
    for r in rows:
        # r may be a SQLAlchemy row - convert explicitly
        exp_type = r.exp_type
        total = float(r.total or 0.0)
        count = int(r.count or 0)
        result.append({"exp_type": exp_type, "total": total, "count": count})

    # sort by absolute total descending (largest movers first)
    result.sort(key=lambda x: abs(x["total"]), reverse=True)
    return result

def _fetch_by_day(db: Session, year: int, month: int) -> List[Dict[str, Any]]:
    """
    Return list of { day: '01', total: float } for days in the month.
    Day is returned as two-digit string to align with frontend examples.
    """
    year_s = str(year)
    month_s = f"{month:02d}"

    q = (
        db.query(
            func.strftime("%d", Expense.tx_datetime).label("day"),
            func.sum(Expense.total_amount).label("total"),
        )
        .filter(func.strftime("%Y", Expense.tx_datetime) == year_s)
        .filter(func.strftime("%m", Expense.tx_datetime) == month_s)
        .group_by(func.strftime("%d", Expense.tx_datetime))
        .order_by(func.strftime("%d", Expense.tx_datetime))
    )

    rows = q.all()
    result = []
    for r in rows:
        day = r.day
        total = float(r.total or 0.0)
        result.append({"day": day, "total": total})
    return result

def get_monthly_report(db: Session, year: int, month: int) -> Dict[str, Any]:
    """
    Return {"year": year, "month": month, "by_category": [...], "by_day": [...]}
    Keeps compatibility with previous shape (by_category), adds by_day for daily chart.
    """
    by_category = _fetch_by_category(db, year, month)
    by_day = _fetch_by_day(db, year, month)
    return {"year": year, "month": month, "by_category": by_category, "by_day": by_day}

def compare_months(db: Session, m1: Tuple[int, int], m2: Tuple[int, int]) -> Dict[str, Any]:
    """
    Compare two months. m1 and m2 are (year, month) tuples.
    Returns:
      {
        "month1": { year, month, by_category, by_day },
        "month2": { ... },
        "diff_by_category": [ { exp_type, total1, total2, diff }, ... ]
      }
    """
    y1, mo1 = m1
    y2, mo2 = m2

    month1 = get_monthly_report(db, y1, mo1)
    month2 = get_monthly_report(db, y2, mo2)

    # build maps of totals for diff
    map1 = {r["exp_type"]: r["total"] for r in month1["by_category"]}
    map2 = {r["exp_type"]: r["total"] for r in month2["by_category"]}
    all_keys = sorted(set(map1.keys()) | set(map2.keys()))

    diff_list = []
    for k in all_keys:
        t1 = float(map1.get(k, 0.0))
        t2 = float(map2.get(k, 0.0))
        diff_list.append({"exp_type": k, "total1": t1, "total2": t2, "diff": t2 - t1})

    # sort by absolute difference descending
    diff_list.sort(key=lambda x: abs(x["diff"]), reverse=True)

    return {"month1": month1, "month2": month2, "diff_by_category": diff_list}
