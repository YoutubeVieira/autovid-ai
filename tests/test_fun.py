"""Mode fun : timeline et texte en ligne de commande."""
import unittest

from autovid.fun import HIT, SLOW, build_timeline


class FunTest(unittest.TestCase):
    def test_timeline_is_monotonic_with_one_slow_and_pause(self):
        tl = build_timeline(n=600, peak=300)
        src = [s for s, _, _ in tl]
        self.assertTrue(all(b >= a for a, b in zip(src, src[1:])))
        phases = [p for _, p, _ in tl]
        self.assertEqual(phases.count("hit"), HIT)
        self.assertEqual(phases[0], "hook")
        self.assertLessEqual(len(tl) / 30, 4.0 + 1.4 / SLOW + HIT / 30 + 6.0 + 0.1)   # clip long : fenêtre bornée

    def test_peak_at_start_still_works(self):
        tl = build_timeline(n=150, peak=20)
        self.assertIn("slow", [p for _, p, _ in tl])
        self.assertGreaterEqual(min(s for s, _, _ in tl), 0)


if __name__ == "__main__":
    unittest.main()
