# tests/test_fresh_modules.py — modulet e vjetra hiqen nga memoria kur ndryshon kodi
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import catalog  # noqa: E402,F401
import fresh_modules  # noqa: E402


class TestFreshModules(unittest.TestCase):
    def test_stale_modules_are_dropped_once(self):
        sys._kpb_code_stamp = None              # si pas një push të ri
        self.assertIn("catalog", sys.modules)
        self.assertTrue(fresh_modules.reload_if_changed())
        self.assertNotIn("catalog", sys.modules)
        import catalog as fresh                 # ngarkohet sërish nga disku
        self.assertTrue(hasattr(fresh, "GOAL_KEYWORDS"))
        self.assertFalse(fresh_modules.reload_if_changed())   # pa ndryshime: asgjë nuk hiqet
        self.assertIn("catalog", sys.modules)


if __name__ == "__main__":
    unittest.main()
