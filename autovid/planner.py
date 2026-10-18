"""Planification : brief → timeline résolue (durées calées sur le tempo, point d'action auto, mise en page)."""
import re
from pathlib import Path

import numpy as np

from .analyze import analyze, beat_track, motion_curve
from .media import FPS, audio_mono, info
from .styles import get_style

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}


def best_window(clip, src_dur):
    """Fenêtre de `src_dur` secondes contenant le plus de mouvement + instant du pic (l'impact)."""
    curve, fps = motion_curve(clip)
    n = max(1, int(round(src_dur * fps)))
    if len(curve) <= n:
        return 0.0, float(np.argmax(curve)) / fps
    smooth = np.convolve(curve, np.ones(3) / 3, mode="same")
    sums = np.convolve(smooth, np.ones(n), mode="valid")
    best = int(np.argmax(sums))
    peak = best + int(np.argmax(smooth[best: best + n]))
    # le pic tombe vers 60 % du plan : on voit la préparation puis l'impact
    start = min(max(peak - int(n * 0.6), 0), len(curve) - n)
    return start / fps, peak / fps


def resolve(brief, base_dir="."):
    base = Path(base_dir)
    style = get_style(brief.get("style", "bincombat"), brief.get("style_overrides"))
    brief = {**brief}
    if brief.get("music"):
        brief["music"] = str((base / brief["music"]).resolve())
    if brief.get("music") and not brief.get("bpm"):
        bt = beat_track(audio_mono(brief["music"]))
        brief["bpm"] = bt["bpm"] or 100
        brief.setdefault("music_offset", bt["beats"][0] if bt["beats"] else 0.0)
    bpm = brief.get("bpm") or 100
    beat = 60.0 / bpm
    if isinstance(brief.get("cta"), str):
        brief["cta"] = {"text": brief["cta"]}

    t_raw, t_prev, segs = 0.0, 0.0, []
    for raw in brief["segments"]:
        seg = {**raw, "clip": str((base / raw["clip"]).resolve())}
        ci = info(seg["clip"])
        dur = seg.get("duration") or seg.get("beats", style["beats_per_shot"]) * beat
        speed = seg.get("speed", 1.0)
        if dur * speed > ci["duration"]:          # plan trop court : ralenti automatique, sinon on raccourcit
            speed = max(0.5, ci["duration"] / dur * 0.98)
            dur = min(dur, ci["duration"] / speed * 0.98)
        seg["speed"] = round(speed, 4)
        if seg.get("layout", "auto") == "auto":
            seg["layout"] = style["landscape_layout"] if ci["width"] >= ci["height"] else "cover"
        if seg.get("start", "auto") == "auto":
            start, peak = best_window(seg["clip"], dur * speed)
            seg["start"] = round(start, 3)
            seg.setdefault("impact", round((peak - start) / speed, 3))
        # coupes arrondies à l'image près sur la grille cumulée : aucune dérive par rapport au tempo
        t_raw += dur
        t_next = round(t_raw * FPS) / FPS
        seg["t0"], seg["t1"], seg["duration"] = t_prev, t_next, round(t_next - t_prev, 4)
        t_prev = t_next
        segs.append(seg)
    brief["segments"] = segs
    brief["total_duration"] = t_prev
    brief["bpm"] = bpm
    return brief


def title_from_name(stem):
    """« 03_mma__smart-back-kick » → kicker « MMA », titre « SMART BACK KICK »."""
    stem = re.sub(r"^\d+[ _.-]*", "", stem)
    parts = [p.replace("-", " ").replace("_", " ").strip().upper() for p in stem.split("__")]
    return (parts[0], parts[1]) if len(parts) > 1 else (None, parts[0])


def auto_brief(clips_dir, style="bincombat", music=None, reference=None, watermark=None, cta=None):
    clips = sorted(p for p in Path(clips_dir).iterdir() if p.suffix.lower() in VIDEO_EXT)
    if not clips:
        raise SystemExit(f"Aucune vidéo trouvée dans {clips_dir}")
    overrides = {}
    if reference:
        dna = analyze(reference)
        print(f"  référence : plan médian {dna['montage']['duree_plan_mediane_s']} s, "
              f"{dna['montage']['temps_par_plan']} temps/plan, {dna['audio']['bpm']} BPM")
        if dna["montage"]["temps_par_plan"]:
            overrides["beats_per_shot"] = max(1, int(round(dna["montage"]["temps_par_plan"])))
        lay = dna["mise_en_page"]
        if lay.get("bandes_noires", 0) > lay.get("fond_flou", 0):
            overrides["landscape_layout"] = "letterbox"
    segments = []
    for i, c in enumerate(clips):
        kicker, title = title_from_name(c.stem)
        seg = {"clip": str(c.resolve()), "kicker": kicker, "title": title}
        if i > 0 and style == "stepbystep":
            seg["transition"] = "flash" if i == 1 else "cut"
        segments.append(seg)
    brief = {"style": style, "segments": segments, "style_overrides": overrides}
    if music:
        brief["music"] = str(Path(music).resolve())
    if watermark:
        brief["watermark"] = watermark
    if cta:
        brief["cta"] = cta
    return brief
