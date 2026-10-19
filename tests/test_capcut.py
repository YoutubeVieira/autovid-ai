"""Effets façon CapCut, vidéo longue et automate viral (sans rendu)."""
import unittest

import numpy as np

from autovid import effets
from autovid.long import chapters_text, order_chapters
from autovid.viral import short_variant


class EffetsTest(unittest.TestCase):
    def test_curves_are_monotonic_and_slow_at_contact(self):
        for name in effets.COURBES:
            before, after = effets.ramp(100, 121, 136, name)
            pos = before + after
            self.assertTrue(all(b > a for a, b in zip(pos, pos[1:])), name)
            self.assertLess(pos[-1], 136)
            self.assertLess(effets.speed_at(name, 0.58, 0.58), 0.5, name)   # ralenti au contact

    def test_transitions_keep_image_valid(self):
        rng = np.random.default_rng(0)
        for kind in effets.TRANSITIONS:
            img = rng.uniform(0, 255, (64, 36, 3)).astype(np.float32)
            effets.transition(img, kind, 0.02, rng)
            self.assertEqual(img.shape, (64, 36, 3))
            self.assertTrue(np.isfinite(img).all(), kind)

    def test_beat_lands_on_hit(self):
        bar = 4 * 60 / 143
        for t in (0.3, 2.0, 7.77):
            off = effets.beat_offset(t)
            self.assertAlmostEqual(((t + off) / bar) % 1 * bar % bar, 0, places=6)


class LongTest(unittest.TestCase):
    def test_best_chapter_two_thirds_and_youtube_format(self):
        an = [{"nom": c, "score": s} for c, s in (("A", 0.2), ("B", 0.9), ("C", 0.3), ("D", 0.1))]
        order = [a["nom"] for a in order_chapters(an)]
        self.assertEqual(order.index("B"), 2)
        txt = chapters_text([(0, "Intro"), (12.4, "1. A"), (75, "2. B")])
        self.assertEqual(txt.splitlines(), ["0:00 Intro", "0:12 1. A", "1:15 2. B"])

    def test_same_move_is_one_chapter(self):
        from autovid.long import group_by_technique
        an = [{"nom": n, "score": sc, "src_t": t} for n, sc, t in (("AÚ", 0.5, 10), ("GINGA", 0.4, 20), ("AÚ", 0.9, 30))]
        g = group_by_technique(an)
        self.assertEqual([x["nom"] for x in g], ["AÚ", "GINGA"])
        self.assertEqual(len(g[0]["items"]), 2)
        self.assertEqual(g[0]["score"], 0.9)

    def test_short_variant_keeps_one_moment(self):
        p = {"analyses": [{"id": 1, "actif": True}, {"id": 2, "actif": True}], "accroche": {"l1": "X"}}
        v = short_variant(p, 2)
        self.assertEqual([a["actif"] for a in v["analyses"]], [False, True])
        self.assertEqual(v["accroche"], {})
        self.assertTrue(p["analyses"][0]["actif"])           # l'original n'est pas modifié


if __name__ == "__main__":
    unittest.main()
