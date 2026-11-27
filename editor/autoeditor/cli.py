"""CLI: python -m autoeditor <analyze|plan|render|qa|run> ..."""
import argparse
import json
import sys
from pathlib import Path

from . import captions as cap
from . import qa as qamod
from .analyze import analyze
from .ff import need_tools, probe
from .plan import build_plan
from .render import render
from .transcribe import transcribe
from . import srt_tools
from .ff import run

PRESETS = Path(__file__).resolve().parent.parent / "presets"


def load_preset(name_or_path):
    p = Path(name_or_path)
    if not p.exists():
        p = PRESETS / f"{name_or_path}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_analyze(a):
    preset = load_preset(a.preset)
    res = analyze(a.input, preset)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if a.out:
        _save(a.out, res)


def _frames_to_video(frames_dir, fps, out):
    """Sequence PNG (f_0001.png ...) -> mp4 sans audio."""
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps), "-i",
         str(Path(frames_dir) / "f_%04d.png"), "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(out)])
    return out


def cmd_run(a):
    need_tools()
    preset = load_preset(a.preset)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    events = []
    if a.events:
        meta = json.loads(Path(a.events).read_text(encoding="utf-8"))
        events = meta["events"]
    src = a.input
    if Path(src).is_dir():
        src = _frames_to_video(src, a.fps, out / "source.mp4")
    info = probe(src)
    print(f"[1/5] analyse ({info['width']}x{info['height']}, {info['duration']:.1f}s)")
    analysis = analyze(src, preset)
    _save(out / "analysis.json", analysis)
    print(f"      {len(analysis['silences'])} silence(s), {len(analysis['scene_cuts'])} changement(s) de plan")

    print("[2/5] transcription")
    srt = a.srt
    if not srt and info["has_audio"] and not a.audio:
        srt = transcribe(src, None, str(out / "transcript.srt"))
    print("      " + (f"sous-titres: {srt}" if srt else "aucune transcription (fournir --srt ou installer faster-whisper)"))

    print("[3/5] plan de montage")
    plan = build_plan(analysis, preset)
    _save(out / "plan.json", plan)
    print(f"      {len(plan['shots'])} plan(s), {plan['removed']:.1f}s coupees, duree finale {plan['output_duration']:.1f}s")

    ass = None
    if srt or a.hook or events or preset.get("outro"):
        ass = out / "captions.ass"
        ass.write_text(cap.build_ass(plan, srt, preset, a.hook, events), encoding="utf-8")
    fonts = None
    fd = preset["captions"].get("fonts_dir")
    if fd:
        fonts = (PRESETS / fd).resolve() if not Path(fd).is_absolute() else Path(fd)

    print("[4/5] rendu")
    final = out / "final.mp4"
    render(plan, src, final, preset, ass_path=ass, music=a.music, has_audio=info["has_audio"],
           voice=a.audio, events=events, sfx_dir=a.sfx_dir, fonts_dir=fonts)

    print("[5/5] controle qualite")
    report = qamod.check(final, preset, plan)
    _save(out / "qa.json", report)
    for c in report["checks"]:
        print(f"      [{'OK' if c['ok'] else 'KO'}] {c['check']}: {c['detail']}")
    print("RESULTAT:", "VALIDE" if report["passed"] else "A CORRIGER", "->", final)
    return 0 if report["passed"] else 1


def cmd_srt(a):
    if a.action == "export":
        n = srt_tools.export_cues(a.input, a.out, a.lang)
        print(f"{n} repliques -> {a.out} (ajouter 'translation' a chaque replique)")
    else:
        n, warns = srt_tools.import_translations(a.input, a.out)
        print(f"{n} repliques -> {a.out}")
        for w in warns:
            print("ATTENTION:", w)


def main(argv=None):
    p = argparse.ArgumentParser(prog="autoeditor", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("analyze", help="analyse une video (silences, plans, loudness)")
    pa.add_argument("input"); pa.add_argument("--preset", default="shortform_9x16"); pa.add_argument("--out")
    pa.set_defaults(fn=cmd_analyze)
    pr = sub.add_parser("run", help="montage complet autonome")
    pr.add_argument("input", help="video, ou dossier d'images f_0001.png"); pr.add_argument("--out-dir", default="out")
    pr.add_argument("--preset", default="shortform_9x16")
    pr.add_argument("--srt", help="sous-titres existants (sinon transcription auto si dispo)")
    pr.add_argument("--hook", help="texte d'accroche affiche dans les premieres secondes")
    pr.add_argument("--music", help="musique de fond (ducking automatique sous la voix)")
    pr.add_argument("--audio", help="voix off (wav) qui remplace l'audio du rush, ex. packs/voices/tts.py")
    pr.add_argument("--events", help="events.json (badges, compteur, coupes) -> HUD, badges et bruitages")
    pr.add_argument("--sfx-dir", default=str(PRESETS.parent.parent / "packs" / "sfx"), help="pack de bruitages")
    pr.add_argument("--fps", type=int, default=24, help="cadence si l'entree est un dossier d'images f_0001.png")
    pr.set_defaults(fn=cmd_run)
    ps = sub.add_parser("srt", help="traduction de sous-titres: export JSON puis reimport en SRT (memes horodatages)")
    ps.add_argument("action", choices=["export", "import"])
    ps.add_argument("input"); ps.add_argument("--out", required=True); ps.add_argument("--lang", default="en")
    ps.set_defaults(fn=cmd_srt)
    a = p.parse_args(argv)
    try:
        return a.fn(a) or 0
    except RuntimeError as e:
        print("ERREUR:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
