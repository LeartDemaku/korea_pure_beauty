# tests/test_database.py
# Teste automatike për Fazën 1 (migrimi dhe funksionet e reja të bazës).
# Nisi nga dosja kryesore e projektit me:  python -m unittest discover tests
import os
import sqlite3
import sys
import tempfile
import unittest

# Lejon importimin e database.py nga dosja prind
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database  # noqa: E402

# Skema e vjetër (para Fazës 1), për të provuar që migrimi nuk humb të dhëna
OLD_SCHEMA = """
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, brand TEXT NOT NULL,
    category TEXT NOT NULL, skin_type TEXT NOT NULL, price REAL NOT NULL, description TEXT,
    eu_certified BOOLEAN DEFAULT 1, is_original BOOLEAN DEFAULT 1, image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT, buyer_name TEXT NOT NULL, phone TEXT NOT NULL,
    city TEXT NOT NULL, address TEXT NOT NULL, items_json TEXT NOT NULL, total_price REAL NOT NULL,
    status TEXT DEFAULT 'E Re (Në Pritje)', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
INSERT INTO products (name, brand, category, skin_type, price) VALUES ('Krem i vjetër', 'COSRX', 'Krem', 'Sensitive', 17.5);
"""


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        # Çdo test merr një bazë të re në një dosje të përkohshme,
        # që baza e vërtetë korea_beauty.db të mos preket kurrë.
        self.tmp = tempfile.TemporaryDirectory()
        self.original_path = database.DATABASE_PATH
        database.DATABASE_PATH = os.path.join(self.tmp.name, 'test.db')

    def tearDown(self):
        database.DATABASE_PATH = self.original_path
        self.tmp.cleanup()


class TestMigration(DatabaseTestCase):
    def test_old_database_keeps_data_and_gets_new_columns(self):
        conn = sqlite3.connect(database.DATABASE_PATH)
        conn.executescript(OLD_SCHEMA)
        conn.close()

        database.init_database()
        database.init_database()  # Duhet të jetë e sigurt edhe kur niset dy herë

        product = database.get_all_products()[0]
        self.assertEqual(product['name'], 'Krem i vjetër')
        self.assertEqual(product['stock_qty'], 0)
        self.assertEqual(product['is_bestseller'], 0)
        self.assertIsNone(product['old_price'])

        conn = sqlite3.connect(database.DATABASE_PATH)
        order_cols = {r[1] for r in conn.execute('PRAGMA table_info(orders)')}
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        self.assertTrue({'tracking_number', 'admin_notes', 'payment_method'} <= order_cols)
        self.assertTrue({'messages', 'store_settings'} <= tables)

    def test_default_settings_do_not_overwrite_admin_changes(self):
        database.init_database()
        database.set_setting('free_shipping_threshold', '40.00')
        database.init_database()
        self.assertEqual(database.get_setting('free_shipping_threshold'), '40.00')


class TestProducts(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        database.init_database()
        self.pid = database.create_product('Serum', 'Anua', 'Serum', 'Mikse', 20.0, stock_qty=5)

    def test_old_style_create_product_still_works(self):
        pid = database.create_product('Toner', 'COSRX', 'Toner', 'E Thatë', 15.0, 'Përshkrim', True, True, '')
        self.assertEqual(database.get_product_by_id(pid)['stock_qty'], 0)

    def test_decrement_stock_never_goes_below_zero(self):
        self.assertTrue(database.decrement_stock(self.pid, 3))
        self.assertFalse(database.decrement_stock(self.pid, 3))  # mbeten vetëm 2
        self.assertEqual(database.get_product_by_id(self.pid)['stock_qty'], 2)

    def test_update_product_fields_rejects_unknown_columns(self):
        with self.assertRaises(ValueError):
            database.update_product_fields(self.pid, price=1, hacker_column='x')

    def test_low_stock_and_bestsellers(self):
        database.update_product_fields(self.pid, stock_qty=2, is_bestseller=1)
        self.assertEqual([p['id'] for p in database.get_low_stock_products()], [self.pid])
        self.assertEqual([p['id'] for p in database.get_bestsellers()], [self.pid])

    def test_discount_percent(self):
        self.assertEqual(database.discount_percent(17.0, 20.0), 15)
        self.assertEqual(database.discount_percent(20.0, None), 0)
        self.assertEqual(database.discount_percent(20.0, 18.0), 0)


class TestMessagesAndOrders(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        database.init_database()

    def test_message_flow(self):
        mid = database.create_message('Arta', 'A keni Anua toner?', email=' ARTA@mail.com ')
        self.assertEqual(database.count_unread_messages(), 1)
        self.assertEqual(database.get_all_messages()[0]['email'], 'arta@mail.com')
        database.update_message_status(mid, 'I Përgjigjur')
        self.assertEqual(database.count_unread_messages(), 0)

    def test_empty_message_is_rejected(self):
        with self.assertRaises(ValueError):
            database.create_message('   ', 'tekst')

    def test_invalid_message_status_is_rejected(self):
        mid = database.create_message('Arta', 'Pyetje')
        with self.assertRaises(ValueError):
            database.update_message_status(mid, 'Status i rremë')

    def test_order_admin_fields(self):
        oid = database.create_order('Arta', '044111222', 'Prishtinë', 'Rr. Agim Ramadani', [], 25.0)
        database.update_order_admin_fields(oid, tracking_number=' KS123 ', admin_notes='Thirr para')
        order = database.get_order_by_id(oid)
        self.assertEqual(order['tracking_number'], 'KS123')
        self.assertEqual(order['payment_method'], 'Para në dorë')


class TestHomePageData(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        database.init_database()

    def test_featured_falls_back_to_newest_products(self):
        first = database.create_product('A', 'Anua', 'Toner', 'Mikse', 10.0)
        second = database.create_product('B', 'COSRX', 'Serum', 'Mikse', 12.0)
        self.assertEqual([p['id'] for p in database.get_featured_products()], [second, first])
        database.update_product_fields(first, is_bestseller=1)
        self.assertEqual([p['id'] for p in database.get_featured_products()], [first])

    def test_testimonials_validation_and_visibility(self):
        database.create_testimonial('Arta', 'Lëkura ime ndihet më e butë.', 5, 'Prishtinë')
        self.assertEqual(len(database.get_visible_testimonials()), 1)
        with self.assertRaises(ValueError):
            database.create_testimonial('Arta', 'Tekst', 6)
        with self.assertRaises(ValueError):
            database.create_testimonial('  ', 'Tekst')


class TestAdminOperations(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        database.init_database()
        self.pid = database.create_product('Serum', 'Anua', 'Serum', 'Mikse', 20.0, stock_qty=5)
        items = [{'product_id': self.pid, 'name': 'Serum', 'qty': 2, 'price': 20.0}]
        self.oid = database.create_order('Arta', '044111222', 'Prishtinë', 'Rr. 1', items, 40.0)
        database.reduce_stock_after_order(self.pid, 2)

    def test_cancel_restores_stock_and_reactivate_takes_it_again(self):
        database.change_order_status(self.oid, 'E Anuluar')
        self.assertEqual(database.get_product_by_id(self.pid)['stock_qty'], 5)
        database.change_order_status(self.oid, 'Në Përpunim')
        self.assertEqual(database.get_product_by_id(self.pid)['stock_qty'], 3)

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            database.change_order_status(self.oid, 'Diçka')

    def test_stock_never_negative_after_order(self):
        database.reduce_stock_after_order(self.pid, 99)
        self.assertEqual(database.get_product_by_id(self.pid)['stock_qty'], 0)

    def test_testimonial_admin_flow(self):
        tid = database.create_testimonial('Arta', 'Shumë e kënaqur.', 5)
        database.set_testimonial_visibility(tid, False)
        self.assertEqual(database.get_visible_testimonials(), [])
        self.assertEqual(len(database.get_all_testimonials()), 1)
        database.delete_testimonial(tid)
        self.assertEqual(database.get_all_testimonials(), [])


if __name__ == '__main__':
    unittest.main()
