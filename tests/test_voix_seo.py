"""Voix off, sous-titres, SEO et miniatures (sans réseau) : python3 -m unittest discover tests"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

from autovid import narration as nar
from autovid import seo, sfx, thumbs
from autovid.anatomy import RISQUES, add_safety, tag_pt


class NarrationTest(unittest.TestCase):
    def test_portuguese_terms_are_tagged(self):
        self.assertEqual(tag_pt("La ginga avant la meia-lua de compasso"),
                         "La [pt]ginga[/pt] avant la [pt]meia-lua de compasso[/pt]")
        self.assertEqual(tag_pt("La rondeur du geste"), "La rondeur du geste")

    def test_script_mentions_muscles_and_risk(self):
        info = add_safety({"nom": "HIGH KICK", "kind": "pied", "muscles": [("PSOAS", "", ()), ("QUADRICEPS", "", ())],
                           "hook": ["A", "B"]})
        txt = nar.script_for(info, 1)
        self.assertIn("psoas et quadriceps", txt)
        self.assertIn(RISQUES["pied"][0].lower(), txt)

    def test_synth_splits_languages_and_times_words(self):
        calls = []

        def fake(piece, voice, lang):
            calls.append((piece, lang))
            chars = [(c, i * 0.05, i * 0.05 + 0.05) for i, c in enumerate(piece)]
            return np.zeros((int(len(piece) * 0.05 * sfx.SR), 2)), chars

        with mock.patch.object(nar, "tts_piece", fake):
            audio, words, dur = nar.synth("Fais la [pt]ginga[/pt] lentement", "v")
        self.assertEqual([c[1] for c in calls], ["fr", "pt", "fr"])
        self.assertEqual([w["text"] for w in words], ["Fais", "la", "ginga", "lentement"])
        self.assertEqual(words[2]["lang"], "pt")
        self.assertTrue(all(b["start"] >= a["end"] - 1e-9 for a, b in zip(words, words[1:])))
        self.assertAlmostEqual(dur, len(audio) / sfx.SR, places=3)

    def test_without_key_words_are_estimated(self):
        segs = [{"id": "hook", "fr": "Regarde sa [pt]ginga[/pt]."}]
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertFalse(nar.voice_segments(segs, voice_id="abc"))
        self.assertIsNone(segs[0]["audio"])
        self.assertEqual([w["text"] for w in segs[0]["words"]], ["Regarde", "sa", "ginga."])

    def test_srt_format(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.srt"
            nar.write_srt(nar.cues_from_text("um dois três quatro", 1.0, 3.0, max_chars=9), p)
            txt = p.read_text()
        self.assertTrue(txt.startswith("1\n00:00:01,000 --> "))
        self.assertIn("00:00:03,000", txt)


class NoCredentialsTest(unittest.TestCase):
    def test_translate_without_credentials_returns_none(self):
        from autovid.ai import translate
        env = {"HOME": "/nonexistent", "PATH": "/usr/bin"}
        with mock.patch.dict("os.environ", env, clear=True):
            self.assertIsNone(translate(["Bonjour"]))


class SeoThumbTest(unittest.TestCase):
    def test_seo_three_languages(self):
        out = seo.build([{"t_out": 0.0, "nom": "HIGH KICK", "kind": "pied", "muscles": []},
                         {"t_out": 65.0, "nom": "DIRECT", "kind": "poing", "muscles": []}], "capoeira", "@moi")
        self.assertEqual(set(out), {"fr", "pt", "en"})
        for d in out.values():
            self.assertTrue(all(len(t) <= 100 for t in d["titres"]))
            self.assertIn("1:05 DIRECT", d["description"])
            self.assertIn("#capoeira", d["hashtags"])
        self.assertIn("[ Anatomie, Placement, Erreurs ]", out["fr"]["titres"][0])

    def test_thumbnail_dna_and_generation(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            img = np.zeros((720, 1280, 3), np.uint8)
            img[:, :, 2] = 90                                  # image sombre et froide
            img[300:420, 700:900] = (255, 140, 40)
            Image.fromarray(img).save(d / "a.jpg")
            dna = thumbs.analyze_folder(d, d / "dna.json")
            self.assertEqual(dna["style"]["temperature"], "froide")
            self.assertEqual(dna["style"]["ambiance"], "sombre / cinématique")
            self.assertTrue(json.loads((d / "dna.json").read_text())["images"])
            frame = np.full((1920, 1080, 3), 120, np.uint8)
            mask = np.zeros((960, 540), np.float32)
            mask[300:700, 200:340] = 1
            yt, cover = thumbs.make_thumbnails(frame, str(d / "t"), "HIGH KICK SECRET", mask=mask)
            with Image.open(yt) as a, Image.open(cover) as b:
                self.assertEqual((a.size, b.size), ((1280, 720), (1080, 1920)))


if __name__ == "__main__":
    unittest.main()
