# tests/test_store_api.py — veprimet e dyqanit: porosia, kontakti, llogaria
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database  # noqa: E402
import store_api  # noqa: E402

DELIVERY = {"name": "Arta Krasniqi", "phone": "+383 44 123 456", "city": "Prishtinë",
            "address": "Rr. Agim Ramadani 5", "notes": "", "email": "", "coupon": ""}


class StoreApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_path = database.DATABASE_PATH
        database.DATABASE_PATH = os.path.join(self.tmp.name, "test.db")
        database.init_database()
        self.pid = database.create_product("Serum", "Anua", "Serum", "Mikse", 20.0, stock_qty=10, size_label="30 ml")
        self.session = {}

    def tearDown(self):
        database.DATABASE_PATH = self.original_path
        self.tmp.cleanup()

    def order(self, items, **extra):
        payload = dict(DELIVERY, items=items, **extra)
        return store_api.handle_event({"id": "x", "type": "place_order", "payload": payload}, self.session)

    def test_order_uses_database_prices_not_browser_prices(self):
        result = self.order([{"id": self.pid, "qty": 2, "price": 0.01}])
        self.assertTrue(result["ok"])
        self.assertEqual(result["order"]["total"], 40.0)  # mbi pragun 30 € -> transport falas
        saved = database.get_order_by_id(result["order"]["id"])
        self.assertEqual(saved["total_price"], 40.0)
        self.assertEqual(database.get_product_by_id(self.pid)["stock_qty"], 8)

    def test_ritual_items_get_ten_percent_and_shipping_is_added(self):
        result = self.order([{"id": self.pid, "qty": 1, "ritual": True}])
        self.assertEqual(result["order"]["total"], 20.0)  # 18.00 + 2.00 transport

    def test_invalid_orders_are_rejected(self):
        self.assertFalse(self.order([])["ok"])
        self.assertFalse(self.order([{"id": self.pid, "qty": 0}])["ok"])
        self.assertFalse(self.order([{"id": self.pid, "qty": 999}])["ok"])
        self.assertFalse(self.order([{"id": "abc", "qty": 1}])["ok"])
        self.assertFalse(self.order([{"id": 9999, "qty": 1}])["ok"])
        bad_phone = dict(DELIVERY, phone="abc")
        result = store_api.handle_event({"id": "y", "type": "place_order",
                                         "payload": dict(bad_phone, items=[{"id": self.pid, "qty": 1}])}, self.session)
        self.assertFalse(result["ok"])
        self.assertEqual(database.get_all_orders(), [])

    def test_coupon(self):
        result = self.order([{"id": self.pid, "qty": 2}], coupon="korea10")
        self.assertEqual(result["order"]["total"], 36.0)

    def test_contact_message(self):
        ok = store_api.handle_event({"type": "contact", "payload": {"name": "Blerta", "email": "b@c.com",
                                                                   "phone": "", "message": "A keni SPF?"}}, {})
        self.assertTrue(ok["ok"])
        self.assertEqual(database.count_unread_messages(), 1)
        bad = store_api.handle_event({"type": "contact", "payload": {"name": "", "message": ""}}, {})
        self.assertFalse(bad["ok"])

    def test_register_verify_logout_flow(self):
        result = store_api.handle_event({"type": "register", "payload": {
            "name": "Sara Hoxha", "email": "Sara@Test.com", "password": "sekret123", "confirm": "sekret123"}}, self.session)
        self.assertTrue(result["ok"])
        self.assertEqual(result["pending_email"], "sara@test.com")
        code = result["test_code"]  # SMTP nuk është konfiguruar në teste
        self.assertEqual(len(code), 6)
        wrong = store_api.handle_event({"type": "verify", "payload": {"email": "sara@test.com", "code": "000000"}}, self.session)
        self.assertFalse(wrong["ok"])
        ok = store_api.handle_event({"type": "verify", "payload": {"email": "sara@test.com", "code": code}}, self.session)
        self.assertTrue(ok["ok"])
        self.assertTrue(self.session["authenticated"])
        self.assertNotIn("password_hash", ok["user"])
        store_api.handle_event({"type": "logout", "payload": {}}, self.session)
        self.assertFalse(self.session["authenticated"])
        login = store_api.handle_event({"type": "login", "payload": {"identifier": "sara@test.com", "password": "sekret123"}}, self.session)
        self.assertTrue(login["ok"])

    def test_page_data_never_exposes_secrets(self):
        user = {"username": "a", "full_name": "A", "email": "a@b.com", "password_hash": "x", "role": "client",
                "verification_code": "123456"}
        data = store_api.build_store_data(lambda path, size, quality: "", user, {})
        self.assertEqual(set(data["user"]), {"name", "email", "is_admin"})
        self.assertEqual(data["products"][0]["size"], "30 ml")
        self.assertEqual(data["featured_ids"], [self.pid])

    def test_unknown_action(self):
        self.assertFalse(store_api.handle_event({"type": "drop_tables"}, {})["ok"])


if __name__ == "__main__":
    unittest.main()
