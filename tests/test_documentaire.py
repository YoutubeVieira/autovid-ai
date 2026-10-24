"""Documentaire : licences, contenu interdit, découpage du plan, chapitres (sans réseau ni rendu)."""
import tempfile
import unittest
from pathlib import Path

from autovid.archives import INTERDIT, Archives, licence_ok
from autovid.documentaire import _segments


class ArchivesTest(unittest.TestCase):
    def test_only_free_licences(self):
        for ok in ("Public domain", "CC0", "CC BY 4.0", "CC BY-SA 3.0", "No known restrictions on publication"):
            self.assertTrue(licence_ok(ok), ok)
        for ko in ("CC BY-NC 2.0", "CC BY-ND 4.0", "CC BY-NC-SA", "All rights reserved", "", "Fair use"):
            self.assertFalse(licence_ok(ko), ko)

    def test_no_graphic_content(self):
        self.assertTrue(INTERDIT.search("Crime scene photo, 1974"))
        self.assertTrue(INTERDIT.search("photo d'autopsie"))
        self.assertFalse(INTERDIT.search("Versailles courthouse, 1921"))

    def test_relevance_rejects_wrong_pictures(self):
        from autovid.archives import pertinence as P
        self.assertTrue(P("Paris street 1916", {"titre": "Paris in 1916.jpg"}))
        self.assertFalse(P("Paris street 1916", {"titre": "Driving boy taking pigs to market", "date": "1915"}))
        self.assertFalse(P("French newspaper 1917", {"titre": "Newspaper fatima 353.jpg"}))
        self.assertFalse(P("Versailles 1920s", {"titre": "[Reel 22] Written records"}))
        self.assertTrue(P("Versailles 1920s", {"titre": "Château de Versailles, 1924"}))
        self.assertFalse(P("Versailles 1920s", {"titre": "Versailles 1960"}))

    def test_local_images_and_offline(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.jpg").write_bytes(b"x")
            arch = Archives(Path(d) / "cache", local=d)
            got = arch.find("anything")
            self.assertEqual(got["type"], "image")
            self.assertIsNone(arch.find("again"))            # chaque image locale sert une fois


class PlanTest(unittest.TestCase):
    def test_segments_order(self):
        plan = {"titre": "T", "accroche": "A", "chapitres": [
            {"titre": "C1", "plans": [{"texte": "x", "visuel": "date", "requete": "", "legende": "1919"}]},
            {"titre": "C2", "plans": [{"texte": "y", "visuel": "archive", "requete": "paris", "legende": ""}]}]}
        kinds = [s["kind"] for s in _segments(plan)]
        self.assertEqual(kinds, ["plan", "carte_titre", "carte_chapitre", "plan", "carte_chapitre", "plan"])


if __name__ == "__main__":
    unittest.main()
