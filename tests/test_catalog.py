# tests/test_catalog.py — filtrat, renditja dhe kuisi i ritualit
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import catalog  # noqa: E402

PRODUCTS = [
    {"id": 1, "name": "Heartleaf Cleansing Foam", "category": "Cleanser (Pastrues)", "skin_type": "E Yndyrshme", "price": 18.5, "created_at": "2026-01-01"},
    {"id": 2, "name": "Master Patch Basic", "category": "Maskë", "skin_type": "Me Akne / Poret", "price": 11.0, "created_at": "2026-01-03"},
    {"id": 3, "name": "Snail Mucin Cream", "category": "Moisturizer (Krem)", "skin_type": "Të gjitha tipet", "price": 17.5, "created_at": "2026-01-02"},
    {"id": 4, "name": "Green Tea Toner", "category": "Toner", "skin_type": "Sensitive", "price": 15.0, "created_at": "2026-01-04"},
]


class TestCatalog(unittest.TestCase):
    def test_category_groups_handle_existing_names(self):
        self.assertEqual(catalog.category_group("Cleanser (Pastrues)"), "Pastrues")
        self.assertEqual(catalog.category_group("Maskë"), "Maska")
        self.assertEqual(catalog.category_group("Moisturizer (Krem)"), "Hidratues & Kremra")
        self.assertEqual(catalog.category_group("Serum / Essence"), "Esenca & Serume")
        self.assertEqual(catalog.category_group("Sunscreen (SPF)"), "Mbrojtës Dielli (SPF)")
        self.assertEqual(catalog.category_group("Eye Cream"), "Hidratues & Kremra")

    def test_all_skin_types_product_matches_every_filter(self):
        self.assertEqual(len(catalog.skin_types_of("Të gjitha tipet")), len(catalog.SKIN_TYPES))
        self.assertEqual(catalog.skin_types_of("E Thata"), ["E Thatë"])
        ids = [p["id"] for p in catalog.filter_products(PRODUCTS, skin_type="E Thatë")]
        self.assertEqual(ids, [3])

    def test_filter_by_category(self):
        ids = [p["id"] for p in catalog.filter_products(PRODUCTS, category="Tonerë")]
        self.assertEqual(ids, [4])

    def test_sorting(self):
        by_price = [p["id"] for p in catalog.sort_products(PRODUCTS, "Çmimi: ulët → lart")]
        self.assertEqual(by_price, [2, 4, 3, 1])
        newest = [p["id"] for p in catalog.sort_products(PRODUCTS, "Më të rejat")]
        self.assertEqual(newest, [4, 2, 3, 1])
        best = [p["id"] for p in catalog.sort_products(PRODUCTS, "Më të shiturat", {"3": 5, "Master Patch Basic": 2})]
        self.assertEqual(best[:2], [3, 2])

    def test_albanian_normalization(self):
        self.assertEqual(catalog.normalize("Kremë Çaji"), "kreme caji")

    def test_ritual_has_four_steps_and_no_duplicates(self):
        routine = catalog.build_ritual(PRODUCTS, "E Yndyrshme", "Trajtim Aknesh", sensitive=False)
        self.assertEqual(len(routine), 4)
        self.assertEqual(routine[0]["product"]["id"], 1)
        self.assertEqual(routine[1]["product"]["id"], 4)
        self.assertEqual(routine[2]["product"]["id"], 2)
        self.assertEqual(routine[3]["product"]["id"], 3)

    def test_ritual_with_missing_category_returns_none(self):
        routine = catalog.build_ritual(PRODUCTS[:1], "Mikse", "Hidratim i Thellë", sensitive=True)
        self.assertIsNone(routine[1]["product"])


class TestStoreTabs(unittest.TestCase):
    def test_tabs_and_badges(self):
        from datetime import date
        self.assertEqual(catalog.store_tab_of(PRODUCTS[0]), "Pastrim & Toner")
        self.assertEqual(catalog.store_tab_of(PRODUCTS[3]), "Pastrim & Toner")
        self.assertEqual([p["id"] for p in catalog.filter_by_tab(PRODUCTS, "Kremra")], [3])
        self.assertEqual(catalog.format_eur(21.9), "21,90 €")
        self.assertEqual(catalog.format_eur(1234.5), "1 234,50 €")
        self.assertEqual(catalog.product_badge({"price": 10, "is_bestseller": 1}), "Më i shituri")
        self.assertEqual(catalog.product_badge({"price": 17, "old_price": 20}), "-15%")
        self.assertEqual(catalog.product_badge({"price": 10, "created_at": "2026-10-20"}, date(2026, 10, 27)), "I ri")
        self.assertEqual(catalog.product_badge({"price": 10, "created_at": "2026-01-01"}, date(2026, 10, 27)), "")


if __name__ == "__main__":
    unittest.main()
