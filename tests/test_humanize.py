"""Nos textes générés passent les règles « humanize » du skill studio-script (pas de tics d'IA)."""
import re
import unittest

from autovid import anatomy, narration, seo

TELLS = [r"\bsecret\b", r"\bsegredo\b", r"en effet", r"crucial", r"essentiel", r"incontournable", r"n'hésite",
         r"révolution", r"game.?changer", r"booster", r"plong", r"—", r"nobody tells", r"personne ne t"]


def tells(text):
    return [t for t in TELLS if re.search(t, text, re.IGNORECASE)]


class HumanizeTest(unittest.TestCase):
    def test_hooks(self):
        for h1, h2 in list(anatomy.HOOKS.values()) + list(anatomy.CAPOEIRA_HOOKS.values()):
            self.assertEqual(tells(h1 + " " + h2), [], (h1, h2))

    def test_seo_titles_and_hashtags(self):
        out = seo.build([{"t_out": 0, "nom": "AÚ", "kind": "au", "muscles": []}], "capoeira", "@moi")
        for lang, d in out.items():
            for t in d["titres"]:
                self.assertEqual(tells(t), [], (lang, t))
            self.assertLessEqual(len(d["hashtags"]), 5, lang)

    def test_outro_single_ask(self):
        segs = narration.build_script([], "combat")
        outro = next(s["fr"] for s in segs if s["id"] == "outro")
        self.assertNotIn("enregistre", outro.lower())


if __name__ == "__main__":
    unittest.main()
