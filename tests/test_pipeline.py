"""Test de bout en bout sur des rushs synthétiques (ffmpeg requis) : python3 -m unittest discover tests"""
import subprocess
import tempfile
import unittest
from pathlib import Path

from autovid.analyze import analyze
from autovid.planner import auto_brief, resolve, title_from_name
from autovid.render import render


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


class PipelineTest(unittest.TestCase):
    def test_title_from_name(self):
        self.assertEqual(title_from_name("03_mma__smart-back-kick"), ("MMA", "SMART BACK KICK"))
        self.assertEqual(title_from_name("question_mark_kick"), (None, "QUESTION MARK KICK"))

    def test_auto_render_is_vertical_and_beat_synced(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "rushs").mkdir()
            ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=3", d / "rushs" / "01_mma__back-kick.mp4")
            ff("-f", "lavfi", "-i", "mandelbrot=s=720x1280:r=30", "-t", "3", d / "rushs" / "02_spin-hook.mp4")
            ff("-f", "lavfi", "-i", "aevalsrc='sin(2*PI*80*t)*exp(-30*mod(t,0.6))':s=44100:d=8", d / "m.wav")
            brief = resolve(auto_brief(d / "rushs", music=d / "m.wav", watermark="Test", cta="SAVE"))
            self.assertAlmostEqual(brief["bpm"], 100, delta=3)
            out = render(brief, d / "out.mp4", d / "work")
            dna = analyze(out)
            self.assertEqual((dna["format"]["width"], dna["format"]["height"]), (1080, 1920))
            self.assertAlmostEqual(dna["format"]["duration"], brief["total_duration"], delta=0.1)
            self.assertEqual(brief["segments"][0]["layout"], "fit_blur")
            self.assertEqual(brief["segments"][1]["layout"], "cover")


if __name__ == "__main__":
    unittest.main()
