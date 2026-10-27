# tests/test_auth_sessions.py
# Teste për rregullimin e sigurisë: kyçja pas F5 bëhet vetëm me token të vlefshëm.
# Nisi nga dosja kryesore e projektit me:  python -m unittest discover tests
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth  # noqa: E402
import database  # noqa: E402


class SessionTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_path = database.DATABASE_PATH
        database.DATABASE_PATH = os.path.join(self.tmp.name, 'test.db')
        database.init_database()
        auth.register_user('admin_test', 'fjalekalim-i-forte', role='admin')
        self.admin = database.get_user_by_username('admin_test')

    def tearDown(self):
        database.DATABASE_PATH = self.original_path
        self.tmp.cleanup()

    def test_valid_token_restores_user(self):
        token = auth.start_session(self.admin)
        self.assertEqual(auth.resume_session(token)['username'], 'admin_test')

    def test_username_is_not_a_valid_token(self):
        # Kjo ishte vrima e vjetër: ?user=admin_test kyçte pa fjalëkalim
        auth.start_session(self.admin)
        self.assertIsNone(auth.resume_session('admin_test'))
        self.assertIsNone(auth.resume_session(None))
        self.assertIsNone(auth.resume_session(''))

    def test_token_is_stored_only_as_hash(self):
        token = auth.start_session(self.admin)
        conn = sqlite3.connect(database.DATABASE_PATH)
        stored = conn.execute('SELECT token_hash FROM sessions').fetchone()[0]
        conn.close()
        self.assertNotEqual(stored, token)
        self.assertEqual(len(stored), 64)

    def test_logout_invalidates_token(self):
        token = auth.start_session(self.admin)
        auth.end_session(token)
        self.assertIsNone(auth.resume_session(token))

    def test_expired_session_is_rejected(self):
        token = auth.start_session(self.admin)
        conn = sqlite3.connect(database.DATABASE_PATH)
        conn.execute("UPDATE sessions SET expires_at = datetime('now', '-1 minute')")
        conn.commit()
        conn.close()
        self.assertIsNone(auth.resume_session(token))

    def test_password_change_logs_out_everywhere(self):
        token = auth.start_session(self.admin)
        ok, _ = auth.change_password_with_current(
            'admin_test', 'fjalekalim-i-forte', 'fjalekalim-i-ri', 'fjalekalim-i-ri')
        self.assertTrue(ok)
        self.assertIsNone(auth.resume_session(token))

    def test_admin_password_must_be_long_enough(self):
        ok, _ = auth.register_user('admin_dobet', '1234', role='admin')
        self.assertFalse(ok)
        self.assertEqual(database.count_admins(), 1)


if __name__ == '__main__':
    unittest.main()
