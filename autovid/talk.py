"""Mode « face caméra » : coupe des silences + recadrage 9:16 + sous-titres dynamiques (ElevenLabs Speech-to-Text)."""
import json
import os
import re
import shutil
from pathlib import Path

from .media import FPS, H, W, info, run
from .render import FONTS_DIR, _ass_time, _esc

STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"


def speech_intervals(path, noise_db=-35, min_silence=0.4, pad=0.08):
    """Intervalles parlés = complément des silences détectés par ffmpeg."""
    out = run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af",
               f"silencedetect=n={noise_db}dB:d={min_silence}", "-f", "null", "-"])
    total = info(path)["duration"]
    starts = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    keep, cursor = [], 0.0
    for s, e in zip(starts, ends + [total] * (len(starts) - len(ends))):
        if s - cursor > 0.05:
            keep.append((max(cursor - pad, 0), min(s + pad, total)))
        cursor = e
    if total - cursor > 0.05:
        keep.append((max(cursor - pad, 0), total))
    return keep or [(0.0, total)]


def cut_silences(path, out, intervals):
    expr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in intervals)
    vf = (f"select='{expr}',setpts=N/FRAME_RATE/TB,fps={FPS},"
          f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1")
    af = f"aselect='{expr}',asetpts=N/SR/TB"
    run(["ffmpeg", "-y", "-v", "error", "-i", path, "-vf", vf, "-af", af, "-c:v", "libx264", "-preset",
         "veryfast", "-crf", "17", "-c:a", "aac", "-b:a", "192k", out])


def transcribe(path, api_key, language=None):
    """Transcription mot à mot via ElevenLabs. Renvoie [{'text', 'start', 'end'}]."""
    import requests
    data = {"model_id": os.environ.get("ELEVENLABS_STT_MODEL", "scribe_v1"), "timestamps_granularity": "word"}
    if language:
        data["language_code"] = language
    with open(path, "rb") as fh:
        r = requests.post(STT_URL, headers={"xi-api-key": api_key}, data=data,
                          files={"file": (Path(path).name, fh)}, timeout=600)
    r.raise_for_status()
    return [{"text": w["text"].strip(), "start": float(w["start"]), "end": float(w["end"])}
            for w in r.json().get("words", []) if w.get("type", "word") == "word" and w["text"].strip()]


def captions_ass(words, path, y=1320, max_words=3, max_gap=0.6):
    """Sous-titres « mot actif » : 1 à 3 mots, le mot prononcé passe en jaune avec un pop."""
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["start"] - cur[-1]["end"] > max_gap):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    events = []
    for chunk in chunks:
        for i, w in enumerate(chunk):
            end = chunk[i + 1]["start"] if i + 1 < len(chunk) else w["end"] + 0.15
            parts = []
            for j, o in enumerate(chunk):
                t = _esc(o["text"].upper())
                parts.append("{\\c&H0000E6FF&\\fscx115\\fscy115\\t(0,90,\\fscx100\\fscy100)}%s{\\r}" % t
                             if j == i else t)
            events.append(f"Dialogue: 0,{_ass_time(w['start'])},{_ass_time(end)},cap,,0,0,0,,"
                          f"{{\\an5\\pos({W // 2},{y})}}" + " ".join(parts))
    Path(path).write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\nStyle: cap,Anton,96,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,"
        "-1,0,0,0,100,100,0,0,1,6,4,5,60,60,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n%s\n" % (W, H, "\n".join(events)), encoding="utf-8")


def talk(src, out, workdir, api_key=None, language=None, noise_db=-35, min_silence=0.4):
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FONTS_DIR, work / "fonts", dirs_exist_ok=True)
    intervals = speech_intervals(src, noise_db, min_silence)
    kept = sum(b - a for a, b in intervals)
    print(f"  {len(intervals)} passages parlés conservés, {info(src)['duration'] - kept:.1f} s de silence retirées")
    cut_silences(src, work / "cut.mp4", intervals)
    vf = "null"
    if api_key:
        run(["ffmpeg", "-y", "-v", "error", "-i", "cut.mp4", "-vn", "-ac", "1", "-b:a", "96k", "voix.mp3"], cwd=work)
        words = transcribe(work / "voix.mp3", api_key, language)
        (work / "mots.json").write_text(json.dumps(words, ensure_ascii=False, indent=1))
        captions_ass(words, work / "sous_titres.ass")
        vf = "ass=sous_titres.ass:fontsdir=fonts"
        print(f"  {len(words)} mots transcrits")
    else:
        print("  (pas de clé ELEVENLABS_API_KEY : rendu sans sous-titres)")
    out_abs = Path(out).resolve()
    run(["ffmpeg", "-y", "-v", "error", "-i", "cut.mp4", "-vf", vf, "-af", "loudnorm=I=-14:TP=-1.0:LRA=7",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-ar", 44100, "-movflags", "+faststart", out_abs], cwd=work)
    return out_abs
