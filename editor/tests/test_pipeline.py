"""Test de bout en bout sur une video synthetique (voix simulee par des sinus + silences)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from autoeditor import cli  # noqa: E402
from autoeditor.analyze import analyze  # noqa: E402
from autoeditor.ff import probe  # noqa: E402
from autoeditor.plan import build_plan, map_time  # noqa: E402

SRT = """1
00:00:00,200 --> 00:00:02,800
Ceci est un test de sous-titres automatiques

2
00:00:04,600 --> 00:00:08,400
Le monteur autonome coupe les silences
"""


def make_input(path):
    # 11 s: son 3s | silence 1.5s | son 4s | silence 0.5s | son 2s
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "lavfi", "-i", "testsrc2=size=640x1138:rate=30:duration=11",
           "-f", "lavfi", "-i", "sine=f=440:d=3", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=1.5",
           "-f", "lavfi", "-i", "sine=f=660:d=4", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=0.5",
           "-f", "lavfi", "-i", "sine=f=550:d=2",
           "-filter_complex", "[1][2][3][4][5]concat=n=5:v=0:a=1[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)]
    subprocess.run(cmd, check=True)


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.src = cls.dir / "in.mp4"
        make_input(cls.src)
        cls.preset = cli.load_preset("shortform_9x16")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_analysis_finds_both_silences(self):
        a = analyze(self.src, self.preset)
        self.assertEqual(len(a["silences"]), 2)
        self.assertAlmostEqual(a["silences"][0][0], 3.0, delta=0.15)

    def test_plan_cuts_silences_and_maps_time(self):
        plan = build_plan(analyze(self.src, self.preset), self.preset)
        self.assertGreater(plan["removed"], 1.6)
        self.assertLess(plan["output_duration"], 9.5)
        self.assertIsNone(map_time(plan, 3.8))  # au milieu du 1er silence
        self.assertIsNotNone(map_time(plan, 1.0))
        self.assertTrue(all(s["src_out"] - s["src_in"] <= self.preset["pacing"]["max_shot"] + 1e-6 for s in plan["shots"]))

    def test_end_to_end_with_captions_hook_and_music(self):
        srt = self.dir / "in.srt"
        srt.write_text(SRT, encoding="utf-8")
        music = self.dir / "music.wav"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        "sine=f=220:d=3", str(music)], check=True)
        out = self.dir / "out"
        rc = cli.main(["run", str(self.src), "--out-dir", str(out), "--srt", str(srt),
                       "--hook", "Test du monteur", "--music", str(music)])
        self.assertEqual(rc, 0)
        info = probe(out / "final.mp4")
        self.assertEqual((info["width"], info["height"]), (1080, 1920))
        plan = json.loads((out / "plan.json").read_text())
        self.assertAlmostEqual(info["duration"], plan["output_duration"], delta=0.3)
        self.assertTrue((out / "captions.ass").read_text().count("Dialogue:") >= 3)
        self.assertTrue(json.loads((out / "qa.json").read_text())["passed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
