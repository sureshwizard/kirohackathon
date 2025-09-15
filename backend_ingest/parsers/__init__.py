from typing import List, Dict

def parse_rows(source: str, rows: List[Dict]) -> List[Dict]:
    """
    Dispatch CSV rows to source-specific parser.
    Each parser returns normalized records:
    {tx_datetime, exp_type, total_amount, note, txn_id}
    """
    src = source.lower()
    if src == "amazon":
        from . import amazon
        return amazon.parse(rows)
    elif src == "gpay":
        from . import gpay
        return gpay.parse(rows)
    elif src == "paytm":
        from . import paytm
        return paytm.parse(rows)
    elif src == "phonepe":
        from . import phonepe
        return phonepe.parse(rows)
    elif src in {"sbi", "hdfc", "icici", "axis"}:
        from . import banks_india
        return banks_india.parse(src, rows)
    elif src in {"chase", "boa"}:
        from . import banks_us
        return banks_us.parse(src, rows)
    elif src in {"td", "rbc"}:
        from . import banks_canada
        return banks_canada.parse(src, rows)
    else:
        from . import generic
        return generic.parse(rows)


def parse_text(source: str, text: str) -> List[Dict]:
    """
    Parse plain-text invoice/bill strings into normalized records.
    """
    from . import generic
    return generic.parse_text(text)
