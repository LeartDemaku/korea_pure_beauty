# analytics.py
# Llogaritjet e Dashboard-it të Admin-it (pa Streamlit, që të testohen).
import json
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

CANCELLED = "E Anuluar"
DONE_STATUSES = {"E Përfunduar / Dorëzuar", "E Marrë / E Dërguar"}


def _order_date(order: dict) -> Optional[date]:
    raw = str(order.get("created_at") or "")[:10]
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def order_items(order: dict) -> List[dict]:
    try:
        return json.loads(order.get("items_json") or "[]")
    except json.JSONDecodeError:
        return []


def kpis(orders: List[dict], products: List[dict], today: Optional[date] = None,
         low_stock_threshold: int = 3) -> Dict[str, float]:
    today = today or date.today()
    valid = [o for o in orders if o.get("status") != CANCELLED]

    def revenue_since(start: date) -> float:
        return round(sum(o["total_price"] for o in valid if (_order_date(o) or date.min) >= start), 2)

    total_revenue = round(sum(o["total_price"] for o in valid), 2)
    return {
        "revenue_total": total_revenue,
        "revenue_today": revenue_since(today),
        "revenue_week": revenue_since(today - timedelta(days=6)),
        "revenue_month": revenue_since(today.replace(day=1)),
        "orders_active": sum(1 for o in valid if o.get("status") not in DONE_STATUSES),
        "orders_total": len(valid),
        "aov": round(total_revenue / len(valid), 2) if valid else 0.0,
        "low_stock": sum(1 for p in products if (p.get("stock_qty") or 0) < low_stock_threshold),
    }


def status_counts(orders: List[dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for order in orders:
        status = order.get("status") or "E Re (Në Pritje)"
        counts[status] = counts.get(status, 0) + 1
    return counts


def daily_sales(orders: List[dict], days: int = 30, today: Optional[date] = None) -> Dict[str, float]:
    """Shitjet për çdo ditë të 30 ditëve të fundit (edhe ditët pa shitje, me 0)."""
    today = today or date.today()
    series = {(today - timedelta(days=offset)).isoformat(): 0.0 for offset in range(days - 1, -1, -1)}
    for order in orders:
        if order.get("status") == CANCELLED:
            continue
        day = _order_date(order)
        if day and day.isoformat() in series:
            series[day.isoformat()] = round(series[day.isoformat()] + order["total_price"], 2)
    return series


def top_products(orders: List[dict], limit: int = 5) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for order in orders:
        if order.get("status") == CANCELLED:
            continue
        for item in order_items(order):
            name = item.get("name", "?").replace(" · Rituali −10%", "")
            counts[name] = counts.get(name, 0) + int(item.get("qty", 0))
    return dict(sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:limit])
