import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "monde"))
import monde  # noqa: E402


class MondeTest(unittest.TestCase):
    def test_parse_formats(self):
        self.assertEqual(monde.parse_line("Léa, boulangère")["prenom"], "Léa")
        self.assertEqual(monde.metier_key(monde.parse_line("Léa, boulangère")["metier_brut"]), "boulanger")
        z = monde.parse_line("Moi c'est Zoé, je veux être astronaute")
        self.assertEqual((z["prenom"], monde.metier_key(z["metier_brut"])), ("Zoé", "astronaute"))
        self.assertEqual(monde.metier_key("pompier"), "pompier")
        self.assertEqual(monde.metier_key("licorne"), "habitant")

    def test_safety_filters(self):
        for bad in ("www.spam.com achetez", "Paul, appelle moi 0612345678", "Tom, nazi", "contact@mail.fr"):
            self.assertFalse(monde.parse_line(bad)["ok"], bad)

    def test_plan_fits_25_30_seconds(self):
        new = [{"prenom": f"P{i}", "metier_dit": m, "look": {"metier": m}} for i, m in enumerate(["pompier", "medecin", "pecheur", "artiste", "sportif", "facteur", "cuisinier", "maire"] * 3)]
        lines, chosen = monde.plan_script("Test", 3, new, 0, len(new))
        self.assertLessEqual(monde.estimate(lines), 30.0)
        self.assertGreaterEqual(len(chosen), 1)
        self.assertTrue(any("manque" in l for l in lines))


if __name__ == "__main__":
    unittest.main()
