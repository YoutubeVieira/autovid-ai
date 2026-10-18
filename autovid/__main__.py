"""AutoVid — monteur vidéo automatique.

  python -m autovid analyze  ref.mp4 -o analyse/            ADN de montage d'une vidéo de référence
  python -m autovid auto     rushs/ -o out.mp4 [--music m.mp3] [--reference ref.mp4] [--style bincombat]
  python -m autovid render   brief.yaml -o out.mp4         montage piloté par un brief (titres, étapes, cercles…)
  python -m autovid talk     face_cam.mp4 -o out.mp4       coupe des silences + sous-titres ElevenLabs
"""
import argparse
import json
import os
import tempfile
from pathlib import Path

from .analyze import analyze, summary
from .planner import auto_brief, resolve
from .render import render
from .styles import STYLES
from .talk import talk


def _load_brief(path):
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith((".yaml", ".yml")):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def _workdir(args, out):
    return args.workdir or tempfile.mkdtemp(prefix=f"autovid_{Path(out).stem}_")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="autovid", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="extraire l'ADN d'une vidéo")
    a.add_argument("videos", nargs="+")
    a.add_argument("-o", "--out", default="analyse")

    au = sub.add_parser("auto", help="montage autonome d'un dossier de rushs")
    au.add_argument("clips_dir")
    au.add_argument("-o", "--out", required=True)
    au.add_argument("--style", choices=list(STYLES), default="bincombat")
    au.add_argument("--music")
    au.add_argument("--reference", help="vidéo dont on copie le rythme et la mise en page")
    au.add_argument("--watermark")
    au.add_argument("--cta", help="texte d'appel à l'action final, ex. « SAVE AND TRY »")
    au.add_argument("--save-brief", help="écrit le brief généré (JSON) pour le retoucher ensuite")
    au.add_argument("--workdir")

    r = sub.add_parser("render", help="rendre un brief YAML/JSON")
    r.add_argument("brief")
    r.add_argument("-o", "--out", required=True)
    r.add_argument("--workdir")

    t = sub.add_parser("talk", help="vidéo face caméra : cut des silences + sous-titres")
    t.add_argument("video")
    t.add_argument("-o", "--out", required=True)
    t.add_argument("--language", help="code langue ISO, ex. fra")
    t.add_argument("--noise-db", type=float, default=-35)
    t.add_argument("--min-silence", type=float, default=0.4)
    t.add_argument("--workdir")

    args = ap.parse_args(argv)
    if args.cmd == "analyze":
        for v in args.videos:
            out = Path(args.out) / Path(v).stem[:40]
            dna = analyze(v, out)
            (out / "resume.md").write_text(summary(dna) + "\n", encoding="utf-8")
            print(summary(dna), f"\n→ {out}/adn.json, planche.jpg\n")
    elif args.cmd == "auto":
        brief = auto_brief(args.clips_dir, args.style, args.music, args.reference, args.watermark, args.cta)
        if args.save_brief:
            Path(args.save_brief).write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
        resolved = resolve(brief)
        print(f"  {len(resolved['segments'])} plans, {resolved['total_duration']:.2f} s @ {resolved['bpm']} BPM")
        print("→", render(resolved, args.out, _workdir(args, args.out)))
    elif args.cmd == "render":
        resolved = resolve(_load_brief(args.brief), Path(args.brief).parent)
        print(f"  {len(resolved['segments'])} plans, {resolved['total_duration']:.2f} s @ {resolved['bpm']} BPM")
        print("→", render(resolved, args.out, _workdir(args, args.out)))
    elif args.cmd == "talk":
        print("→", talk(args.video, args.out, _workdir(args, args.out), os.environ.get("ELEVENLABS_API_KEY"),
                        args.language, args.noise_db, args.min_silence))


if __name__ == "__main__":
    main()
