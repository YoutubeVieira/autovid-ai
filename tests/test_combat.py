"""Tests rapides du mode combat (sans MediaPipe) : python3 -m unittest discover tests"""
import unittest

import numpy as np

from autovid import sfx
from autovid.anatomy import classify
from autovid.combat import build_timeline, detect_impacts, freeze_len
from autovid.pose import L_ANK, L_HIP, L_KNEE, L_SH, NOSE, R_ANK, R_HIP, R_KNEE, R_SH, R_WR
from autovid.talk import clean_words


def standing(n=90):
    """Personne debout, immobile : (2, n, 33, 3)."""
    p = np.full((33, 3), np.nan)
    pts = {NOSE: (0.5, 0.25), L_SH: (0.55, 0.35), R_SH: (0.45, 0.35), L_HIP: (0.53, 0.55), R_HIP: (0.47, 0.55),
           L_KNEE: (0.54, 0.7), R_KNEE: (0.46, 0.7), L_ANK: (0.55, 0.85), R_ANK: (0.45, 0.85)}
    for j in range(33):
        p[j] = (0.5, 0.5, 0.9)
    for j, (x, y) in pts.items():
        p[j] = (x, y, 0.95)
    tr = np.full((2, n, 33, 3), np.nan)
    tr[0] = p
    return tr


class CombatTest(unittest.TestCase):
    def test_high_kick_is_detected_and_named(self):
        tr = standing()
        # la cheville droite monte d'un coup au-dessus des épaules entre les images 40 et 46
        for j, i in enumerate(range(40, 47)):
            tr[0, i, R_ANK, :2] = (0.45 - 0.05 * j, 0.85 - 0.09 * j)
            tr[0, i, R_KNEE, :2] = (0.46 - 0.03 * j, 0.7 - 0.05 * j)
        tr[0, 47:, R_ANK, :2] = tr[0, 46, R_ANK, :2]
        tr[0, 47:, R_KNEE, :2] = tr[0, 46, R_KNEE, :2]
        imps = detect_impacts(tr, cuts_frames=[])
        self.assertEqual(len(imps), 1)
        info = classify(tr[0], imps[0]["frame"], imps[0]["eff"])
        self.assertEqual(info["nom"], "HIGH KICK")
        self.assertEqual(info["membre"], "JAMBE DROITE")
        self.assertEqual(len(info["muscles"]), 3)

    def test_footwork_is_not_a_kick(self):
        tr = standing()
        for j, i in enumerate(range(40, 47)):          # le pied glisse vite au sol : déplacement, pas un coup
            tr[0, i, L_ANK, :2] = (0.55 + 0.05 * j, 0.85)
        tr[0, 47:, L_ANK, :2] = tr[0, 46, L_ANK, :2]
        self.assertEqual(detect_impacts(tr, cuts_frames=[]), [])

    def test_cut_jumps_are_ignored(self):
        tr = standing()
        tr[0, 50:] += np.array([0.3, 0.0, 0.0])        # le squelette « saute » sur une coupe
        self.assertEqual(detect_impacts(tr, cuts_frames=[50]), [])

    def test_punch_detected(self):
        tr = standing()
        for j, i in enumerate(range(30, 36)):
            tr[0, i, R_WR, :2] = (0.45 - 0.06 * j, 0.36)
        tr[0, 36:, R_WR, :2] = tr[0, 35, R_WR, :2]
        imps = detect_impacts(tr, cuts_frames=[])
        self.assertEqual(len(imps), 1)
        self.assertEqual(classify(tr[0], imps[0]["frame"], imps[0]["eff"])["kind"], "poing")

    def test_capoeira_variants(self):
        from autovid.anatomy import add_safety, capoeira_variant
        tr = standing()
        base = classify(tr[0], 10, R_ANK)
        # aú : pieds au-dessus de la tête, mains au sol
        au = tr[0, 10].copy()
        au[[L_ANK, R_ANK], 1] = 0.1
        au[[15, 16], 1] = 0.9
        self.assertEqual(capoeira_variant(au[None], 0, dict(base))["nom"], "AÚ")
        # esquiva : bassin sous les genoux
        low = tr[0, 10].copy()
        low[[L_HIP, R_HIP], 1] = 0.75
        info = capoeira_variant(low[None], 0, {**base, "kind": "poing", "nom": "DIRECT"})
        self.assertEqual(info["nom"], "ESQUIVA")
        for nom, attendu in (("HIGH KICK", "MEIA-LUA DE COMPASSO"), ("LOW KICK", "RASTEIRA")):
            got = add_safety(capoeira_variant(tr[0, 10][None], 0, {**base, "kind": "pied", "nom": nom}))
            self.assertEqual(got["nom"], attendu)
            self.assertTrue(got["risque"][0])

    def test_timeline_structure(self):
        tr = standing(300)
        imp = {"frame": 150, "track": 0, "eff": R_ANK, "score": 0.5}
        imp["info"] = classify(tr[0], 150, R_ANK)
        tl = build_timeline(300, [imp], hook=True)
        phases = [f["phase"] for f in tl]
        self.assertEqual(phases[0], "hook_slow")
        for ph in ("hook_freeze", "jump", "slow", "freeze", "post", "outro"):
            self.assertIn(ph, phases)
        self.assertEqual(phases.count("freeze"), int(freeze_len(imp) * 30))
        main = [f["src"] for f in tl if not f["phase"].startswith("hook")]
        self.assertTrue(all(b >= a for a, b in zip(main, main[1:])), "la partie principale doit être monotone")
        self.assertLess(len(tl) / 30, 20)

    def test_sounds_are_finite_and_bounded(self):
        for name, fn in sfx.LIB.items():
            s = fn()
            self.assertEqual(s.shape[1], 2, name)
            self.assertTrue(np.isfinite(s).all(), name)
            self.assertLess(np.abs(s).max(), 1.5, name)
        m = sfx.music(3)
        self.assertEqual(m.shape, (3 * sfx.SR, 2))

    def test_clean_words_keeps_last_retake(self):
        w = lambda t, a: {"text": t, "start": a, "end": a + 0.3}  # noqa: E731
        words = [w("Bon", 0), w("euh", 0.4), w("on", 1), w("va", 1.3), w("voir", 1.6),
                 w("on", 3), w("va", 3.3), w("voir", 3.6), w("ça", 3.9)]
        self.assertEqual([x["text"] for x in clean_words(words)], ["Bon", "on", "va", "voir", "ça"])


class ServerSecurityTest(unittest.TestCase):
    def test_token_required_and_paths_confined(self):
        import json
        import tempfile
        import threading
        import urllib.error
        import urllib.request
        from http.server import ThreadingHTTPServer
        from pathlib import Path

        from autovid import server

        with tempfile.TemporaryDirectory() as d:
            server.Handler.token = "secret"
            server.Handler.data_dir = Path(d)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{httpd.server_port}"
            try:
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(base + "/api/jobs")
                self.assertEqual(e.exception.code, 403)
                req = urllib.request.Request(base + "/api/jobs?k=secret", method="POST",
                                             data=json.dumps({"video": "/etc/passwd"}).encode())
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(req)
                self.assertEqual(e.exception.code, 400)
                req = urllib.request.Request(base + "/api/upload?name=../../evil.sh&k=secret", method="POST", data=b"x")
                with self.assertRaises(urllib.error.HTTPError):
                    urllib.request.urlopen(req)
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
