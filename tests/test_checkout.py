# tests/test_checkout.py — transporti, kuponi dhe kontrolli i të dhënave të dërgesës
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import checkout  # noqa: E402

SETTINGS = {"shipping_fee": "2.00", "free_shipping_threshold": "30.00"}


class TestCheckout(unittest.TestCase):
    def test_shipping_below_and_above_threshold(self):
        self.assertEqual(checkout.calculate_totals(20.0, SETTINGS)["total"], 22.0)
        self.assertEqual(checkout.calculate_totals(30.0, SETTINGS)["shipping"], 0.0)
        self.assertEqual(checkout.calculate_totals(20.0, SETTINGS)["missing_for_free_shipping"], 10.0)

    def test_coupon_is_case_insensitive(self):
        totals = checkout.calculate_totals(50.0, SETTINGS, " korea10 ")
        self.assertEqual(totals["discount"], 5.0)
        self.assertEqual(totals["total"], 45.0)

    def test_bad_settings_fall_back_to_defaults(self):
        self.assertEqual(checkout.shipping_rules({"shipping_fee": "abc"}), (2.0, 30.0))

    def test_delivery_validation(self):
        self.assertEqual(checkout.validate_delivery("Arta Krasniqi", "+383 44 123 456", "Prishtinë", "Rr. Agim Ramadani 5"), [])
        errors = checkout.validate_delivery("A", "abc", "", "x", "jo-email")
        self.assertEqual(len(errors), 5)

    def test_whatsapp_link(self):
        self.assertTrue(checkout.whatsapp_link("+383 45 319 619", "Përshëndetje").startswith("https://wa.me/38345319619?text="))
        self.assertEqual(checkout.whatsapp_link("", "x"), "")


if __name__ == "__main__":
    unittest.main()
