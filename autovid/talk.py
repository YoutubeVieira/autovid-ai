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
    data = {"model_id": os.environ.get("ELEVENLABS_STT_MODEL", "scribe_v2"), "timestamps_granularity": "word"}
    if language:
        data["language_code"] = language
    with open(path, "rb") as fh:
        r = requests.post(STT_URL, headers={"xi-api-key": api_key}, data=data,
                          files={"file": (Path(path).name, fh)}, timeout=600)
    r.raise_for_status()
    return [{"text": w["text"].strip(), "start": float(w["start"]), "end": float(w["end"])}
            for w in r.json().get("words", []) if w.get("type", "word") == "word" and w["text"].strip()]


FILLERS = {"euh", "heu", "euhh", "hum", "hmm", "bah", "ben", "beh", "hein", "uh", "um", "erm"}


def _norm(w):
    return re.sub(r"[^\w']", "", w.lower())


def clean_words(words, window=8.0, n=3):
    """Retire les « euh » et les faux départs : si une phrase redémarre par les mêmes mots, on garde la dernière."""
    words = [w for w in words if _norm(w["text"]) not in FILLERS]
    drop = set()
    for i in range(len(words) - n):
        key = [_norm(w["text"]) for w in words[i: i + n]]
        for j in range(i + 1, len(words) - n + 1):
            if words[j]["start"] - words[i]["start"] > window:
                break
            if [_norm(w["text"]) for w in words[j: j + n]] == key:
                drop.update(range(i, j))          # tout ce qui précède la reprise
                break
    return [w for k, w in enumerate(words) if k not in drop]


def word_intervals(words, pad=0.06, join=0.35):
    out = []
    for w in words:
        a, b = max(w["start"] - pad, 0), w["end"] + pad
        if out and a - out[-1][1] < join:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def remap(words, intervals):
    """Recale les temps des mots après le montage des intervalles conservés."""
    res, offset = [], 0.0
    for a, b in intervals:
        for w in words:
            if a <= w["start"] < b:
                res.append({**w, "start": w["start"] - a + offset, "end": min(w["end"], b) - a + offset})
        offset += b - a
    return res


def captions_ass(words, path, y=1320, max_words=3, max_gap=0.6, highlight=True):
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
                             if j == i and highlight else t)
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
    src_cut = "cut.mp4"
    if api_key:
        run(["ffmpeg", "-y", "-v", "error", "-i", "cut.mp4", "-vn", "-ac", "1", "-b:a", "96k", "voix.mp3"], cwd=work)
        words = transcribe(work / "voix.mp3", api_key, language)
        cleaned = clean_words(words)
        print(f"  {len(words)} mots transcrits, {len(words) - len(cleaned)} retirés (euh, faux départs)")
        if len(cleaned) < len(words) and cleaned:
            keep = word_intervals(cleaned)
            cut_silences(work / "cut.mp4", work / "clean.mp4", keep)
            cleaned = remap(cleaned, keep)
            src_cut = "clean.mp4"
        (work / "mots.json").write_text(json.dumps(cleaned, ensure_ascii=False, indent=1))
        captions_ass(cleaned, work / "sous_titres.ass")
        vf = "ass=sous_titres.ass:fontsdir=fonts"
    else:
        print("  (pas de clé ELEVENLABS_API_KEY : rendu sans sous-titres)")
    out_abs = Path(out).resolve()
    run(["ffmpeg", "-y", "-v", "error", "-i", src_cut, "-vf", vf, "-af", "loudnorm=I=-14:TP=-1.0:LRA=7",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-ar", 44100, "-movflags", "+faststart", out_abs], cwd=work)
    return out_abs
