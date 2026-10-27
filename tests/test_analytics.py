# tests/test_analytics.py — KPI-të e Dashboard-it
import json
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analytics  # noqa: E402

TODAY = date(2026, 10, 27)
ORDERS = [
    {"total_price": 30.0, "status": "E Re (Në Pritje)", "created_at": "2026-10-27 10:00:00",
     "items_json": json.dumps([{"name": "Toner", "qty": 2}])},
    {"total_price": 20.0, "status": "E Përfunduar / Dorëzuar", "created_at": "2026-10-22 09:00:00",
     "items_json": json.dumps([{"name": "Krem · Rituali −10%", "qty": 1}, {"name": "Toner", "qty": 1}])},
    {"total_price": 99.0, "status": "E Anuluar", "created_at": "2026-10-27 11:00:00",
     "items_json": json.dumps([{"name": "Serum", "qty": 9}])},
    {"total_price": 10.0, "status": "Në Përpunim", "created_at": "2026-09-30 08:00:00", "items_json": "i dëmtuar"},
]
PRODUCTS = [{"stock_qty": 0}, {"stock_qty": 2}, {"stock_qty": 10}]


class TestAnalytics(unittest.TestCase):
    def test_kpis_ignore_cancelled_orders(self):
        result = analytics.kpis(ORDERS, PRODUCTS, TODAY)
        self.assertEqual(result["revenue_total"], 60.0)
        self.assertEqual(result["revenue_today"], 30.0)
        self.assertEqual(result["revenue_week"], 50.0)
        self.assertEqual(result["revenue_month"], 50.0)
        self.assertEqual(result["orders_active"], 2)
        self.assertEqual(result["aov"], 20.0)
        self.assertEqual(result["low_stock"], 2)

    def test_daily_sales_has_every_day(self):
        series = analytics.daily_sales(ORDERS, 30, TODAY)
        self.assertEqual(len(series), 30)
        self.assertEqual(series["2026-10-27"], 30.0)
        self.assertEqual(series["2026-10-26"], 0.0)

    def test_top_products_merges_ritual_items_and_survives_bad_json(self):
        self.assertEqual(analytics.top_products(ORDERS), {"Toner": 3, "Krem": 1})

    def test_empty_shop(self):
        self.assertEqual(analytics.kpis([], [], TODAY)["aov"], 0.0)


if __name__ == "__main__":
    unittest.main()
