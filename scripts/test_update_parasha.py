"""Check calendar boundaries, repository links, and exceptional readings."""

import unittest
from datetime import date
from urllib.parse import unquote

from update_parasha import (
    DOUBLES, NAMES, ROOT, build_pages, build_reading, upcoming_shabbat,
)


class ReadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = build_pages()

    def reading(self, title, day=date(2026, 11, 14)):
        return build_reading({"items": [{
            "date": day.isoformat(), "category": "parashat",
            "title": "Parashat " + title,
        }]}, day, "off", self.pages)

    def test_every_link_has_a_repository_page(self):
        self.assertEqual(len(NAMES), 54)
        self.assertEqual(len(self.pages), 61)
        for portions in self.pages.values():
            for portion in portions:
                path = ROOT / unquote(portion["url"]).strip("/") / "README.md"
                self.assertTrue(path.is_file(), path)

    def test_spelling_variants(self):
        for hebcal, local in [("Shmini", "Shemini"), ("Sh’lach", "Shlach Lecha"),
                              ("Vaera", "Va'era"), ("Beha’alotcha", "BehaAlotcha")]:
            self.assertEqual(self.reading(hebcal)["portions"][0]["name"], local)

    def test_all_double_portions_and_single_hyphenated_name(self):
        for first, second in DOUBLES:
            title = f"{NAMES[first - 1]}-{NAMES[second - 1]}"
            self.assertEqual(len(self.reading(title)["portions"]), 2)
        self.assertEqual(len(self.reading("Lech-Lecha")["portions"]), 1)

    def test_week_and_year_boundaries(self):
        for current, expected in [("2026-11-08", "2026-11-14"),
                                  ("2026-11-14", "2026-11-14"),
                                  ("2026-11-15", "2026-11-21"),
                                  ("2026-12-31", "2027-01-02")]:
            self.assertEqual(upcoming_shabbat(date.fromisoformat(current)).isoformat(),
                             expected)

    def test_festival_replaces_regular_portion(self):
        day = date(2026, 4, 4)
        data = build_reading({"items": [{
            "date": day.isoformat(), "category": "holiday", "title": "Pesach III (CH''M)",
            "leyning": {"torah": "Exodus 33:12-34:26"},
        }]}, day, "on", self.pages)
        self.assertEqual(data["portions"], [])
        self.assertIn("Pesach", data["festival"])
        self.assertEqual(data["cycle"], "Israel")

    def test_missing_and_unknown_readings_fail(self):
        with self.assertRaises(ValueError):
            build_reading({"items": []}, date(2026, 11, 14), "off", self.pages)
        with self.assertRaises(ValueError):
            self.reading("Unknown portion")
        with self.assertRaises(ValueError):
            build_reading({"items": {}}, date(2026, 11, 14), "off", self.pages)


if __name__ == "__main__":
    unittest.main()
