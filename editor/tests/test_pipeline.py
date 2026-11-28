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


class PixelPresetAndSrtTest(unittest.TestCase):
    def test_pixel_game_hud_badges_sfx_outro(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src = tmp / "frames"
            src.mkdir()
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                            "testsrc2=size=450x800:rate=24:duration=3", str(src / "f_%04d.png")], check=True)
            ev = tmp / "events.json"
            ev.write_text(json.dumps({"fps": 24, "events": [
                {"t": 0.5, "type": "counter", "value": 1, "label": "1"},
                {"t": 0.5, "type": "badge", "text": "+1 HABITANT", "color": "yellow"},
                {"t": 1.5, "type": "cut"}]}), encoding="utf-8")
            voice = tmp / "voice.wav"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                            "sine=f=300:d=3", str(voice)], check=True)
            rc = cli.main(["run", str(src), "--out-dir", str(tmp / "o"), "--preset", "pixel_game",
                           "--events", str(ev), "--audio", str(voice)])
            self.assertEqual(rc, 0)
            plan = json.loads((tmp / "o" / "plan.json").read_text())
            self.assertAlmostEqual(plan["output_duration"], plan["content_duration"] + 2.2, delta=0.01)
            ass = (tmp / "o" / "captions.ass").read_text()
            self.assertIn("1 / 100", ass)
            self.assertIn("+1 HABITANT", ass)
            self.assertIn("LA VILLE DES", ass)

    def test_srt_roundtrip_keeps_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "a.srt").write_text(SRT, encoding="utf-8")
            cli.main(["srt", "export", str(tmp / "a.srt"), "--out", str(tmp / "c.json"), "--lang", "en"])
            data = json.loads((tmp / "c.json").read_text())
            for c in data["cues"]:
                c["translation"] = "Hello " + c["text"][:10]
            (tmp / "c.json").write_text(json.dumps(data), encoding="utf-8")
            cli.main(["srt", "import", str(tmp / "c.json"), "--out", str(tmp / "b.srt")])
            out = (tmp / "b.srt").read_text()
            self.assertIn("00:00:00,200 --> 00:00:02,800", out)
            self.assertIn("00:00:04,600 --> 00:00:08,400", out)


class CorrectorTest(unittest.TestCase):
    def test_audio_fix_clipped_quiet_leading_silence(self):
        from autoeditor import corrector as co
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src, dst = tmp / "a.wav", tmp / "b.wav"
            # 1 s de silence + sinus tres fort (ecrete) de 3 s
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=1",
                            "-f", "lavfi", "-i", "sine=f=440:d=3", "-filter_complex", "[1]volume=9,alimiter=limit=1:level=disabled[s];[0][s]concat=n=2:v=0:a=1",
                            str(src)], check=True)
            preset = cli.load_preset("shortform_9x16")
            before, after = co.fix_audio(src, dst, preset)
            codes = {i["code"] for i in before["issues"]}
            self.assertIn("silence_debut", codes)
            self.assertTrue(codes & {"volume", "crete", "saturation"})
            self.assertTrue(after["ok"])
            self.assertAlmostEqual(after["mesures"]["lufs"], -14.0, delta=1.5)
            self.assertLess(after["mesures"]["duree"], before["mesures"]["duree"])   # le silence de debut est rogne

    def test_video_fix_format_black_head_and_sync(self):
        from autoeditor import corrector as co
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src, dst = tmp / "v.mp4", tmp / "w.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=640x480:r=25:d=1",
                            "-f", "lavfi", "-i", "testsrc2=s=640x480:r=25:d=3", "-f", "lavfi", "-i", "sine=f=330:d=4",
                            "-filter_complex", "[0][1]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-pix_fmt", "yuv444p",
                            "-c:a", "aac", "-shortest", str(src)], check=True)
            preset = cli.load_preset("shortform_9x16")
            before, after = co.fix_video(src, dst, preset)
            codes = {i["code"] for i in before["issues"]}
            self.assertTrue({"format", "noir_debut", "pix_fmt"} <= codes)
            self.assertEqual((after["mesures"]["width"], after["mesures"]["height"]), (1080, 1920))
            self.assertNotIn("noir_debut", {i["code"] for i in after["issues"]})
            self.assertEqual(after["mesures"]["pix_fmt"], "yuv420p")
            self.assertTrue(after["ok"])
