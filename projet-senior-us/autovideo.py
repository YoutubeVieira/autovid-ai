#!/usr/bin/env python3
"""Auto Video Senior (US) — générateur de séances de gym douce pour YouTube.

Commandes :
  plan    --minutes 10|20|30 --focus balance|strength|mobility --out sessions/x.json
  check   sessions/x.json              timeline, durée totale, avertissements
  still   sessions/x.json --at 12.5    image de contrôle (coach + habillage)
  render  sessions/x.json [--preview] [--alpha] [--until S]
          → out/<slug>/<slug>.mp4, youtube/, capcut/

Style (kit « Gym Douce Senior ») : coach plein écran, textes posés sur la vidéo avec
un halo doux, sans cadre ; chronomètre calculé depuis les heures de début/fin de chaque
segment, jamais par un minuteur indépendant.
"""
import argparse
import csv
import hashlib
import json
import math
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------- configuration

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Brand:
    def __init__(self, path=ROOT / "config" / "brand.json"):
        self.cfg = load_json(path)
        self.W, self.H = self.cfg["resolution"]
        self.fps = self.cfg["fps"]
        self.c = {k: hex_rgb(v) for k, v in self.cfg["colors"].items()}
        self.copy = self.cfg["copy"]
        self.anim = self.cfg["animation"]
        self.layout = self.cfg["layout"]
        self._fonts = {}

    def font(self, role, size):
        key = (role, size)
        if key not in self._fonts:
            path, weight = self.cfg["fonts"][role]
            f = ImageFont.truetype(str(ROOT / path), size)
            try:
                f.set_variation_by_name(weight)
            except (OSError, ValueError):
                pass  # police statique : la graisse est celle du fichier
            self._fonts[key] = f
        return self._fonts[key]


# ---------------------------------------------------------------- timeline

def build_timeline(session, brand):
    """Ajoute start/end, numéro d'exercice et exercice suivant à chaque segment."""
    t = 0.0
    segs = []
    total_ex = sum(1 for s in session["segments"] if s["type"] == "exercise")
    n = 0
    for s in session["segments"]:
        s = dict(s)
        if s["type"] == "exercise":
            n += 1
        s["index"] = n
        s["total"] = total_ex
        s["start"], s["end"] = t, t + float(s["duration"])
        t = s["end"]
        segs.append(s)
    for i, s in enumerate(segs):
        s["next"] = next((x for x in segs[i + 1:] if x["type"] == "exercise"), None)
    return segs, t


def say_lines(seg, brand):
    """Lignes de voix off d'un segment : [(début absolu, texte)]."""
    off = brand.cfg["voice"]["offset"]
    say = seg.get("say")
    if seg["type"] == "intro" and not say:
        c = brand.copy
        say = [{"at": 0.2, "text": " ".join(c["intro_lines"])}, {"at": 4.5, "text": c["intro_chair"]}]
    if seg["type"] == "outro" and not say:
        c = brand.copy
        say = [{"at": 0.3, "text": f'{c["outro_title"]} {c["outro_line"]}'}]
    if not say:
        return []
    if isinstance(say, str):
        say = [{"at": off, "text": say}]
    return [(seg["start"] + float(x.get("at", off)), x["text"]) for x in say]


def fmt_ts(t, srt=False):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}" if srt else (f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}")


# ---------------------------------------------------------------- éléments graphiques

class Element:
    """Image RGBA (float32, alpha non prémultiplié) + position du coin haut-gauche."""

    def __init__(self, arr, x, y):
        self.arr, self.x, self.y = arr, int(round(x)), int(round(y))


_cache = {}


def text_block(brand, text, role, size, color, max_w=None, halo=True, line_gap=1.18, align="center"):
    key = ("txt", text, role, size, color, max_w, halo, align)
    if key in _cache:
        return _cache[key]
    font = brand.font(role, size)
    words, lines = text.split(), []
    for w in words:
        if lines and max_w and font.getlength(lines[-1] + " " + w) <= max_w:
            lines[-1] += " " + w
        elif lines and not max_w:
            lines[-1] += " " + w
        else:
            lines.append(w)
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * line_gap)
    tw = int(max(font.getlength(l) for l in lines)) if lines else 1
    pad = 30 if halo else 4
    W, H = tw + 2 * pad, lh * len(lines) + 2 * pad
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for i, l in enumerate(lines):
        lw = font.getlength(l)
        x = pad + {"center": (tw - lw) / 2, "left": 0, "right": tw - lw}[align]
        d.text((x, pad + i * lh), l, font=font, fill=255)
    out = np.zeros((H, W, 4), np.float32)
    m = np.asarray(mask, np.float32) / 255.0
    if halo:
        # Halo doux couleur beige au lieu d'un rectangle (règle 6 du kit).
        h = np.asarray(mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14)), np.float32) / 255.0
        h = np.clip(h * 0.75, 0, 0.75)
        # Texte clair (sur fond sombre) : halo sombre ; texte olive : halo beige.
        light = color == brand.c["white"]
        out[..., :3] = np.array((36, 48, 40) if light else brand.c["beige"], np.float32) / 255.0
        out[..., 3] = h * (0.8 if light else 1.0)
    col = np.array(color, np.float32) / 255.0
    a = m + out[..., 3] * (1 - m)
    safe = np.where(a > 0, a, 1)
    out[..., :3] = (col * m[..., None] + out[..., :3] * (out[..., 3] * (1 - m))[..., None]) / safe[..., None]
    out[..., 3] = a
    _cache[key] = (out, pad)
    return out, pad


def place(arr, pad, x, y, anchor):
    """anchor : 'tl' (haut-gauche), 'tr', 'tc' — coordonnées du texte, sans la marge du halo."""
    h, w = arr.shape[:2]
    tw = w - 2 * pad
    if anchor == "tc":
        x -= tw / 2
    elif anchor == "tr":
        x -= tw
    return Element(arr, x - pad, y - pad)


def bar_element(brand, x_center, y, width, progress):
    h = 7
    fw = int(width * max(0.0, min(1.0, progress)))
    key = ("bar", width, fw)  # mis en cache par largeur remplie : images identiques réutilisées
    if key not in _cache:
        img = Image.new("RGBA", (width + 8, h + 8), (*brand.c["white"], 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((4, 4, 4 + width, 4 + h), radius=h // 2, fill=(*brand.c["white"], 150))
        if fw > h:
            d.rounded_rectangle((4, 4, 4 + fw, 4 + h), radius=h // 2, fill=(*brand.c["sage"], 255))
        _cache[key] = np.asarray(img, np.float32) / 255.0
    return Element(_cache[key], x_center - width / 2 - 4, y - 4)


def leaf_icon(brand, size=30):
    key = ("leaf", size)
    if key not in _cache:
        s = size * 4
        img = Image.new("RGBA", (s, s), (*brand.c["sage"], 0))
        d = ImageDraw.Draw(img)
        d.ellipse((s * 0.15, s * 0.05, s * 0.85, s * 0.75), fill=(*brand.c["sage"], 255))
        d.ellipse((s * 0.40, s * -0.20, s * 1.25, s * 0.55), fill=(*brand.c["sage"], 0))
        d.line((s * 0.2, s * 0.95, s * 0.6, s * 0.35), fill=(*brand.c["olive"], 255), width=int(s * 0.06))
        img = img.resize((size, size), Image.LANCZOS)
        _cache[key] = np.asarray(img, np.float32) / 255.0
    return _cache[key]


def dot_icon(color, size=18):
    key = ("dot", color, size)
    if key not in _cache:
        img = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
        ImageDraw.Draw(img).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=(*color, 255))
        _cache[key] = np.asarray(img.resize((size, size), Image.LANCZOS), np.float32) / 255.0
    return _cache[key]


def arrow_element(brand, W, H, spec):
    key = ("arrow", spec["dir"])
    if key not in _cache:
        L, th = 150, 16
        img = Image.new("RGBA", (L + 40, L + 40), (*brand.c["sage"], 0))  # fond transparent de même teinte : pas de liseré sombre au flou
        d = ImageDraw.Draw(img)
        c = (*brand.c["sage"], 235)
        m = (L + 40) // 2
        # Flèche vers le haut, tournée ensuite selon la direction.
        d.line((m, L + 10, m, 50), fill=c, width=th)
        d.polygon([(m, 10), (m - 38, 62), (m + 38, 62)], fill=c)
        rot = {"up": 0, "left": 90, "down": 180, "right": -90}[spec["dir"]]
        img = img.rotate(rot, resample=Image.BICUBIC)
        img = img.filter(ImageFilter.GaussianBlur(0.6))
        _cache[key] = np.asarray(img, np.float32) / 255.0
    arr = _cache[key]
    h, w = arr.shape[:2]
    return Element(arr, spec["x"] * W - w / 2, spec["y"] * H - h / 2)


def fade(t, t0, t1, fin, fout):
    """Opacité : fondu d'entrée sur fin s après t0, de sortie sur fout s avant t1."""
    if t < t0 or t >= t1:
        return 0.0
    a = 1.0
    if fin > 0:
        a = min(a, (t - t0) / fin)
    if fout > 0:
        a = min(a, (t1 - t) / fout)
    return max(0.0, min(1.0, a))


# ---------------------------------------------------------------- habillage d'une image

LUMA_W, LUMA_H = 96, 54  # carte de luminosité du décor, une par segment
DARK_BG = 135


def overlay_elements(t, segs, brand, total):
    """Liste (Element, opacité) à l'instant t. Tout est dérivé de start/end des segments."""
    seg = next((s for s in segs if s["start"] <= t < s["end"]), segs[-1])
    W, H = brand.W, brand.H
    M = brand.layout["safe_margin"]
    side = seg.get("text_side", brand.layout["text_side"])
    cx = brand.layout["column_center_x"] if side == "right" else W - brand.layout["column_center_x"]
    colw = brand.layout["column_width"]
    an = brand.anim
    els = []
    s0, s1 = seg["start"], seg["end"]
    loc = t - s0
    luma = seg.get("_luma")

    def T(text, role, size, x, y, anchor, max_w=None, grey=False):
        """Texte posé sur la vidéo : olive sur décor clair, blanc sur décor sombre (règle du kit).

        Le ton est choisi pour chaque texte d'après le décor juste derrière lui ;
        "text_tone": "light" | "dark" sur un segment force le choix.
        """
        dark = (brand.c["warm_grey"] if grey else brand.c["olive"])
        light = ((226, 232, 226) if grey else brand.c["white"])
        e = place(*text_block(brand, text, role, size, dark, max_w=max_w), x, y, anchor)
        tone = seg.get("text_tone")
        if tone is None and luma is not None:
            h, w = e.arr.shape[:2]
            x0, y0 = max(0, e.x * LUMA_W // W), max(0, e.y * LUMA_H // H)
            x1, y1 = min(LUMA_W, (e.x + w) * LUMA_W // W + 1), min(LUMA_H, (e.y + h) * LUMA_H // H + 1)
            tone = "light" if luma[y0:y1, x0:x1].mean() < DARK_BG else "dark"
        if tone == "light":
            e = place(*text_block(brand, text, role, size, light, max_w=max_w), x, y, anchor)
        return e

    if seg["type"] == "intro":
        f = an["intro_fade"]
        els.append((T(brand.cfg["name"], "title", 74, cx, 330, "tc"), fade(t, s0, s0 + 1.9, f, f)))
        promise = seg.get("promise") or ""
        if promise:
            els.append((T(promise, "title", 60, cx, 360, "tc", colw), fade(t, s0 + 1.5, s0 + 4.6, f, f)))
        chair = seg.get("chair_line", brand.copy["intro_chair"])
        els.append((T(chair, "instruction", 44, cx, 400, "tc", colw), fade(t, s0 + 4.5, s1, f, f)))
        return els

    if seg["type"] == "outro":
        f = an["intro_fade"]
        a = fade(t, s0, s1, f, 0.8)
        els.append((T(brand.copy["outro_title"], "title", 80, cx, 330, "tc"), a))
        els.append((T(brand.copy["outro_line"], "instruction", 46, cx, 440, "tc", colw), a))
        els.append((T(brand.copy["subscribe"], "instruction", 32, W - M, H - M - 40, "tr"), fade(t, s0 + 1.5, s1, f, 0.8)))
        return els

    # Repères discrets permanents pendant la séance (pas de cadre).
    els.append((T(brand.cfg["name"].upper(), "title", 28, M, M - 10, "tl"), 0.9))
    num = seg["index"] if seg["type"] == "exercise" else (seg["next"]["index"] if seg["next"] else seg["index"])
    els.append((T(f'{num:02d} / {seg["total"]:02d}', "timer", 30, W - M, M - 10, "tr"), 0.85))

    rest = seg["type"] == "rest"
    f = an["rest_fade"] if rest else an["title_fade"]
    a = fade(t, s0, s1, f, f)
    title = brand.copy["rest_title"] if rest else seg["name"].upper()
    els.append((T(title, "title", 54, cx, 300, "tc", colw), a))

    if seg.get("reps"):
        k = min(seg["reps"], int(loc / seg["duration"] * seg["reps"]) + 1)
        counter = f'{k:02d} / {seg["reps"]:02d}'
    else:
        remaining = max(0, math.ceil(s1 - t - 1e-6))
        counter = f"{remaining // 60:02d}:{remaining % 60:02d}"
    els.append((T(counter, "timer", 150, cx, 370, "tc"), a))
    els.append((bar_element(brand, cx, 560, 400, loc / seg["duration"]), a))
    if seg.get("instruction"):
        els.append((T(seg["instruction"], "instruction", 42, cx, 600, "tc", colw), a))
    if rest and seg["next"]:
        nxt = brand.copy["next"].format(name=seg["next"]["name"])
        els.append((T(nxt, "instruction", 32, cx, 730, "tc", colw, grey=True), fade(t, s0 + 1.0, s1, f, f)))

    # Encouragement / conseil en bas, sans bandeau.
    cue = seg.get("cue")
    if rest and seg.get("safety"):
        e = T(brand.copy["safety"], "instruction", 30, W - M, H - M - 36, "tr")
        ca = fade(t, s0 + 1.0, s1, 0.5, 0.5)
        els.append((e, ca))
        els.append((Element(dot_icon(brand.c["soft_yellow"], 18), e.x, e.y + 41), ca))
    elif cue:
        e = T(cue, "instruction", 32, W - M, H - M - 38, "tr")
        ca = fade(t, s0 + 2.0, s1, 0.5, 0.5)
        els.append((e, ca))
        els.append((Element(leaf_icon(brand, 32), e.x - 14, e.y + 34), ca))

    arrow = seg.get("arrow")
    if arrow:
        at = s0 + float(arrow.get("at", 2.0))
        els.append((arrow_element(brand, W, H, arrow), fade(t, at, at + an["arrow_seconds"], 0.25, 0.25)))
    return els


def attach_luma(seg, gray_small):
    """gray_small : image en niveaux de gris LUMA_W×LUMA_H du décor au milieu du segment."""
    seg["_luma"] = np.asarray(gray_small, np.float32).reshape(LUMA_H, LUMA_W)


def compose(els, W, H):
    """Superpose les éléments (alpha 'over') sur un calque transparent → uint8 RGBA.

    Le calcul flottant ne porte que sur la zone de chaque élément, pas sur l'image entière.
    """
    canvas = np.zeros((H, W, 4), np.uint8)
    for e, op in els:
        if op <= 0:
            continue
        h, w = e.arr.shape[:2]
        x0, y0 = max(e.x, 0), max(e.y, 0)
        x1, y1 = min(e.x + w, W), min(e.y + h, H)
        if x1 <= x0 or y1 <= y0:
            continue
        src = e.arr[y0 - e.y:y1 - e.y, x0 - e.x:x1 - e.x]
        dst = canvas[y0:y1, x0:x1].astype(np.float32) / 255.0
        sa = src[..., 3:4] * op
        da = dst[..., 3:4]
        oa = sa + da * (1 - sa)
        safe = np.where(oa > 0, oa, 1)
        rgb = (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / safe
        canvas[y0:y1, x0:x1] = (np.concatenate([rgb, oa], axis=-1) * 255 + 0.5).astype(np.uint8)
    return canvas


# ---------------------------------------------------------------- coach, audio

def placeholder_coach(brand, path):
    """Fond doux + silhouette, quand aucune vidéo du coach n'est fournie."""
    W, H = brand.W, brand.H
    img = Image.new("RGB", (W, H), brand.c["beige"])
    d = ImageDraw.Draw(img)
    top, bottom = np.array((252, 251, 247)), np.array(brand.c["beige"]) * 0.97
    for y in range(H):
        d.line((0, y, W, y), fill=tuple(int(v) for v in top + (bottom - top) * (y / H)))
    d.rectangle((0, int(H * 0.82), W, H), fill=(226, 214, 196))
    x = int(W * 0.36)
    sil = (*brand.c["warm_grey"],)
    d.ellipse((x - 55, 170, x + 55, 290), fill=sil)
    d.rounded_rectangle((x - 95, 300, x + 95, 610), radius=60, fill=sil)
    d.rounded_rectangle((x - 80, 590, x - 15, 900), radius=30, fill=sil)
    d.rounded_rectangle((x + 15, 590, x + 80, 900), radius=30, fill=sil)
    d.text((x - 90, 940), "COACH", font=brand.font("instruction", 34), fill=brand.c["warm_grey"])
    img.save(path)
    return path


def is_image(p):
    return Path(p).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}


def build_coach(segs, session, brand, work, until=None):
    """Concatène les plans du coach (vidéo ou image) en coach.mp4 sans son."""
    default = session.get("coach_default")
    placeholder = None
    groups = []  # (source, durée) en regroupant les segments consécutifs de même source
    for s in segs:
        if until is not None and s["start"] >= until:
            break
        dur = s["duration"] if until is None else min(s["end"], until) - s["start"]
        src = s.get("coach") or default
        if not src:
            placeholder = placeholder or str(placeholder_coach(brand, work / "coach_placeholder.png"))
            src = placeholder
        else:
            src = str((ROOT / src) if not Path(src).is_absolute() else Path(src))
        if groups and groups[-1][0] == src:
            groups[-1][1] += dur
        else:
            groups.append([src, dur])
    args, filt = [], []
    for i, (src, dur) in enumerate(groups):
        if is_image(src):
            args += ["-loop", "1", "-framerate", str(brand.fps), "-t", f"{dur:.3f}", "-i", src]
        else:
            args += ["-stream_loop", "-1", "-t", f"{dur:.3f}", "-i", src]
        filt.append(
            f"[{i}:v]scale={brand.W}:{brand.H}:force_original_aspect_ratio=increase,crop={brand.W}:{brand.H},"
            f"fps={brand.fps},setsar=1,format=yuv420p,trim=duration={dur:.3f},setpts=PTS-STARTPTS[v{i}]"
        )
    filt.append("".join(f"[v{i}]" for i in range(len(groups))) + f"concat=n={len(groups)}:v=1:a=0[out]")
    out = work / "coach.mp4"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args, "-filter_complex", ";".join(filt),
         "-map", "[out]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-an", str(out)])
    return out


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def tts_file(text, brand, work):
    cmd = brand.cfg["tts"].get("command")
    if not cmd:
        return None
    out = work / "tts" / (hashlib.sha1(text.encode()).hexdigest()[:16] + ".mp3")
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        parts = [p.replace("{text}", text).replace("{out}", str(out)) for p in shlex.split(cmd)]
        run(parts)
    return out


def voice_plan(segs, brand, work, use_tts=True):
    """[(début, fin, texte, fichier audio ou None)] — sert à la fois à l'audio et au SRT."""
    wps = brand.cfg["voice"]["words_per_second"]
    plan = []
    for s in segs:
        lines = say_lines(s, brand)
        for i, (t0, text) in enumerate(lines):
            audio = None
            if s.get("voice") and i == 0:
                audio = ROOT / s["voice"]
            elif use_tts:
                audio = tts_file(text, brand, work)
            dur = probe_duration(audio) if audio else len(text.split()) / wps + 0.4
            limit = lines[i + 1][0] if i + 1 < len(lines) else s["end"]
            plan.append((t0, min(t0 + dur, limit), text, audio))
    return plan


def build_audio(plan, total, brand, work):
    args = ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    filt, labels, n = [], ["[0:a]"], 1
    for t0, _, _, audio in plan:
        if not audio:
            continue
        args += ["-i", str(audio)]
        ms = int(t0 * 1000)
        filt.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{n}]")
        labels.append(f"[a{n}]")
        n += 1
    music = brand.cfg["music"]
    if music.get("file"):
        args += ["-stream_loop", "-1", "-t", f"{total:.3f}", "-i", str(ROOT / music["file"])]
        filt.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,volume={music['volume']},"
                    f"afade=t=in:d=2,afade=t=out:st={max(0, total - 3):.3f}:d=3[m]")
        labels.append("[m]")
    filt.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,alimiter=limit=0.95[out]")
    out = work / "audio.m4a"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args, "-filter_complex", ";".join(filt),
         "-map", "[out]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out)])
    return out


# ---------------------------------------------------------------- sorties YouTube / CapCut

def write_srt(plan, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, (t0, t1, text, _) in enumerate(plan, 1):
            f.write(f"{i}\n{fmt_ts(t0, True)} --> {fmt_ts(t1, True)}\n{text}\n\n")


def chapters(segs, brand):
    """Chapitres YouTube : un par exercice, repos rattachés à l'exercice précédent."""
    out = []
    for s in segs:
        if s["type"] == "intro":
            out.append((0.0, "Welcome"))
        elif s["type"] == "exercise":
            out.append((s["start"], s["name"]))
        elif s["type"] == "outro":
            out.append((s["start"], "Well Done!"))
    # YouTube : premier chapitre à 00:00, chacun d'au moins 10 s. Un chapitre trop court
    # est fusionné avec le suivant (« Welcome & March in Place »), pas supprimé.
    merged = []
    for i, (t, name) in enumerate(out):
        nxt = out[i + 1][0] if i + 1 < len(out) else None
        if merged and merged[-1][2]:
            merged[-1] = (merged[-1][0], f"{merged[-1][1]} & {name}", False)
            continue
        merged.append((t, name, nxt is not None and nxt - t < 10))
    return [(0.0 if i == 0 else t, n) for i, (t, n, _) in enumerate(merged)]


def write_youtube(session, segs, total, brand, ydir):
    ydir.mkdir(parents=True, exist_ok=True)
    chap = chapters(segs, brand)
    lines = [session.get("title", ""), "", session.get("description", session.get("promise", "")), ""]
    if len(chap) >= 3:
        lines += [f"{fmt_ts(t)} {n}" for t, n in chap] + [""]
    lines += ["⚠️ " + brand.copy["disclaimer"], "", " ".join(session.get("hashtags", ["#seniorfitness", "#chairexercise", "#gentleworkout"]))]
    (ydir / "description.txt").write_text("\n".join(lines), encoding="utf-8")
    (ydir / "title.txt").write_text(session.get("title", "") + "\n", encoding="utf-8")


def write_capcut_readme(cdir, slug, alpha):
    txt = f"""# Import into CapCut (desktop or web)

CapCut has no public upload API: this folder is prepared so you can drag it into CapCut
(or into CapCut Cloud space) and fine-tune by hand.

| File | Use in CapCut |
|------|---------------|
| `{slug}_final.mp4` | Finished video, ready for YouTube. Import only this if no changes are needed. |
| `{slug}_clean.mp4` | Coach + voice + music, **without** on-screen text. Main track for re-editing. |
| `captions.en.srt` | Captions → *Captions / Text → Import captions* (desktop/web only, UTF-8). You can also run CapCut *Text to speech* on these captions to get a voice-over. |
| `stills/*.png` | Transparent PNG of each segment's text (reference or overlay track). |
| `timeline.csv` | Start/end of every segment, to line up PNGs or cuts. |
"""
    if alpha:
        txt += f"| `{slug}_overlay_alpha.mov` | All text + timers with an alpha channel (QuickTime Animation or ProRes 4444). Place above `{slug}_clean.mp4`. Check transparency with a short test: if the background turns black in your CapCut version, use `{slug}_final.mp4` instead. |\n"
    txt += """
Steps:
1. New project → 16:9 (1920×1080), 30 fps.
2. Import `*_clean.mp4` to the main track (or `*_final.mp4` if you only want to add music/intro).
3. Import `captions.en.srt` (optional — YouTube also accepts the same file as closed captions).
4. Export 1080p, 30 fps, H.264.
"""
    (cdir / "IMPORT_CAPCUT.md").write_text(txt, encoding="utf-8")


# ---------------------------------------------------------------- commandes

def run(cmd, **kw):
    try:
        return subprocess.run(cmd, check=True, **kw)
    except subprocess.CalledProcessError as e:
        sys.exit(f"Échec : {' '.join(map(str, cmd[:6]))}… (code {e.returncode})")


def load_session(path, brand):
    session = load_json(path)
    segs, total = build_timeline(session, brand)
    for s in segs:
        if s["type"] == "intro":
            s.setdefault("promise", session.get("promise"))
    return session, segs, total


def cmd_check(a):
    brand = Brand()
    session, segs, total = load_session(a.session, brand)
    warn = []
    print(f'{session.get("title", "")}\n')
    for s in segs:
        label = s.get("name") or s["type"]
        print(f'{fmt_ts(s["start"])}–{fmt_ts(s["end"])}  {s["type"]:<8} {label}')
        hi = 120 if s.get("section") == "cooldown" else 60  # étirements tenus plus longtemps
        if s["type"] == "exercise" and not 20 <= s["duration"] <= hi:
            warn.append(f'{label} : {s["duration"]} s (kit : 30–45 s, étirements ≤ 120 s)')
        if s["type"] == "rest" and s["duration"] < 15:
            warn.append(f'repos de {s["duration"]} s avant {s["next"]["name"] if s["next"] else "la fin"} (kit : ≥ 15 s)')
        if len(s.get("instruction", "")) > 48:
            warn.append(f'{label} : consigne longue ({len(s["instruction"])} car.) — une consigne courte à la fois')
    if segs[0]["type"] != "intro":
        warn.append("pas d'intro")
    if not any(s.get("safety") for s in segs):
        warn.append("aucun rappel de sécurité à l'écran (ajouter \"safety\": true à un repos)")
    target = session.get("target_minutes")
    print(f"\nDurée totale : {fmt_ts(total)}" + (f" (cible {target} min)" if target else ""))
    if target and abs(total - target * 60) > 5:
        warn.append(f"écart à la cible : {total - target * 60:+.0f} s")
    for w in warn:
        print("⚠", w)
    return 0


def cmd_still(a):
    brand = Brand()
    session, segs, total = load_session(a.session, brand)
    work = ROOT / "out" / session["slug"] / "work"
    work.mkdir(parents=True, exist_ok=True)
    seg = next(s for s in segs if s["start"] <= a.at < s["end"])
    src = seg.get("coach") or session.get("coach_default")
    if src and not is_image(src):
        frame = work / "still_bg.png"
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{(a.at - seg['start']):.3f}", "-i", str(ROOT / src),
             "-frames:v", "1", str(frame)])
        bg = Image.open(frame)
    else:
        bg = Image.open(ROOT / src) if src else Image.open(placeholder_coach(brand, work / "coach_placeholder.png"))
    bg = bg.convert("RGB")
    k = max(brand.W / bg.width, brand.H / bg.height)
    bg = bg.resize((math.ceil(bg.width * k), math.ceil(bg.height * k)))
    bg = bg.crop(((bg.width - brand.W) // 2, (bg.height - brand.H) // 2, (bg.width - brand.W) // 2 + brand.W, (bg.height - brand.H) // 2 + brand.H))
    attach_luma(seg, bg.convert("L").resize((LUMA_W, LUMA_H), Image.BOX))
    ov = Image.fromarray(compose(overlay_elements(a.at, segs, brand, total), brand.W, brand.H), "RGBA")
    out = Path(a.out or work / f"still_{a.at:.1f}.png")
    Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB").save(out)
    print(out)


def cmd_render(a):
    brand = Brand()
    session, segs, total = load_session(a.session, brand)
    slug = session["slug"]
    base = ROOT / "out" / slug
    work, cdir, ydir = base / "work", base / "capcut", base / "youtube"
    for d in (work, cdir / "stills", ydir):
        d.mkdir(parents=True, exist_ok=True)
    end = min(total, a.until) if a.until else total
    W, H, fps = brand.W, brand.H, brand.fps

    print("1/4 coach…")
    coach = build_coach(segs, session, brand, work, until=end if a.until else None)

    for seg in segs:
        mid = (seg["start"] + seg["end"]) / 2
        if mid < end:
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{mid:.3f}", "-i", str(coach), "-frames:v", "1",
                                "-vf", f"scale={LUMA_W}:{LUMA_H}:flags=area", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                               capture_output=True)
            if len(r.stdout) == LUMA_W * LUMA_H:
                attach_luma(seg, np.frombuffer(r.stdout, np.uint8))
    print("2/4 voix off, sous-titres, musique…")
    plan = voice_plan(segs, brand, work, use_tts=not a.no_tts)
    plan = [p for p in plan if p[0] < end]
    write_srt(plan, ydir / "captions.en.srt")
    shutil.copy(ydir / "captions.en.srt", cdir / "captions.en.srt")
    audio = build_audio(plan, end, brand, work)

    print("3/4 habillage + encodage…")
    final = cdir / f"{slug}_final.mp4"
    scale = ",scale=960:540" if a.preview else ""
    filt = "[0:v][1:v]overlay=0:0:format=auto" + scale + ",format=yuv420p[v]"
    outs = ["-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", "veryfast" if a.preview else "medium",
            "-crf", "23" if a.preview else "18", "-r", str(fps), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", "-t", f"{end:.3f}", str(final)]
    if a.alpha:
        # qtrle (« Animation ») : sans perte, ~7× plus léger que ProRes 4444 sur un calque surtout vide.
        codec = (["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"] if a.alpha == "prores"
                 else ["-c:v", "qtrle", "-pix_fmt", "argb"])
        filt = "[1:v]split[o1][o2];[0:v][o1]overlay=0:0:format=auto" + scale + ",format=yuv420p[v]"
        outs += ["-map", "[o2]", *codec, "-t", f"{end:.3f}", str(cdir / f"{slug}_overlay_alpha.mov")]
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(coach),
         "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(fps), "-i", "pipe:0",
         "-i", str(audio), "-filter_complex", filt, *outs],
        stdin=subprocess.PIPE,
    )
    frames = int(round(end * fps))
    prev_key, prev = None, None
    for i in range(frames):
        t = i / fps
        els = overlay_elements(t, segs, brand, total)
        # Images identiques (aucun fondu en cours, même seconde, même barre) : on réutilise.
        key = tuple((id(e.arr), e.x, e.y, round(op, 3)) for e, op in els)
        if key != prev_key:
            prev, prev_key = compose(els, W, H).tobytes(), key
        proc.stdin.write(prev)
        if i % (fps * 30) == 0:
            print(f"   {fmt_ts(t)} / {fmt_ts(end)}", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("Échec de l'encodage FFmpeg")

    print("4/4 dossiers YouTube et CapCut…")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(coach), "-i", str(audio), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-t", f"{end:.3f}", str(cdir / f"{slug}_clean.mp4")])
    with open(cdir / "timeline.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["start", "end", "type", "name", "instruction"])
        for s in segs:
            if s["start"] < end:
                wr.writerow([fmt_ts(s["start"]), fmt_ts(min(s["end"], end)), s["type"], s.get("name", ""), s.get("instruction", "")])
                mid = s["start"] + min(s["duration"], end - s["start"]) / 2
                Image.fromarray(compose(overlay_elements(mid, segs, brand, total), W, H), "RGBA").save(
                    cdir / "stills" / f'{fmt_ts(s["start"]).replace(":", "-")}_{s["type"]}.png')
    write_capcut_readme(cdir, slug, a.alpha)
    write_youtube(session, segs, total, brand, ydir)
    shutil.copy(final, base / f"{slug}.mp4")
    print(f"\n✔ {base / (slug + '.mp4')}  ({fmt_ts(end)})\n✔ {ydir}/\n✔ {cdir}/")


def cmd_plan(a):
    """Construit une séance 10/20/30 min à partir de la bibliothèque d'exercices."""
    brand = Brand()
    lib = load_json(ROOT / "config" / "exercises.json")
    pick = lambda sec: [e for e in lib if e["section"] == sec and a.focus in e["focus"]] or [e for e in lib if e["section"] == sec]
    budget = {10: (120, 345), 20: (180, 870), 30: (270, 1305)}[a.minutes]  # échauffement, bloc principal (s)
    effort, rest_s = (35, 18) if a.minutes == 10 else (40, 20)
    segs = [{"type": "intro", "duration": 7}]

    def exercise(e, duration, rnd):
        seg = {k: e[k] for k in ("name", "instruction", "cue", "say") if k in e}
        seg.update(type="exercise", duration=duration, section=e["section"])
        if rnd > 1:
            seg["name"] += f" (Round {rnd})"
        if "arrow" in e:
            seg["arrow"] = e["arrow"]
        return seg

    def add(pool, seconds, eff, with_rest):
        """k exercices (+ repos entre chacun) ; on reprend la liste en « Round 2 » si elle est trop courte."""
        step = eff + (rest_s if with_rest else 0)
        k = max(1, (seconds + (rest_s if with_rest else 0)) // step)
        if not with_rest:
            # Échauffement : un passage par exercice, durées allongées plutôt que répétées (max 45 s).
            k = min(k, len(pool))
            eff = min(45, seconds // k)
        for i in range(k):
            segs.append(exercise(pool[i % len(pool)], eff, i // len(pool) + 1))
            if with_rest and i < k - 1:
                segs.append({"type": "rest", "duration": rest_s, "instruction": "Relax your shoulders and breathe",
                             "say": "Take a short rest. Relax your shoulders, and breathe."})
        return k * eff + (k - 1) * rest_s if with_rest else k * eff

    w = add(pick("warmup"), budget[0], 30, False)
    m = add(pick("main"), budget[1], effort, True)
    cool_total = a.minutes * 60 - 7 - w - m - 8
    cool = pick("cooldown")
    n = max(1, min(len(cool), round(cool_total / 35)))
    for i, e in enumerate(cool[:n]):
        d = cool_total // n + (cool_total % n if i == n - 1 else 0)
        segs.append({"type": "exercise", "section": "cooldown", "duration": d,
                     **{k: e[k] for k in ("name", "instruction", "cue", "say")}})
    segs.append({"type": "outro", "duration": 8})
    first_rest = next((s for s in segs if s["type"] == "rest"), None)
    if first_rest:
        first_rest["safety"] = True
    focus_word = {"balance": "Balance", "strength": "Strength", "mobility": "Mobility"}[a.focus]
    session = {
        "slug": f"{a.focus}-{a.minutes}min",
        "title": f"{a.minutes}-Minute Gentle {focus_word} Workout for Seniors | Chair Support Option",
        "promise": f"{a.minutes} minutes to work on your {a.focus}",
        "description": f"A gentle {a.minutes}-minute {a.focus} routine for seniors. Follow along at your own pace — a sturdy chair is all you need.",
        "target_minutes": a.minutes,
        "coach_default": None,
        "hashtags": ["#seniorfitness", f"#{a.focus}exercises", "#chairexercise", "#over60"],
        "segments": segs,
    }
    out = Path(a.out or ROOT / "sessions" / f"{session['slug']}.json")
    out.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("plan")
    pl.add_argument("--minutes", type=int, choices=[10, 20, 30], default=10)
    pl.add_argument("--focus", choices=["balance", "strength", "mobility"], default="balance")
    pl.add_argument("--out")
    ck = sub.add_parser("check")
    ck.add_argument("session")
    st = sub.add_parser("still")
    st.add_argument("session")
    st.add_argument("--at", type=float, required=True)
    st.add_argument("--out")
    rd = sub.add_parser("render")
    rd.add_argument("session")
    rd.add_argument("--preview", action="store_true", help="960×540, encodage rapide")
    rd.add_argument("--alpha", nargs="?", const="qtrle", choices=["qtrle", "prores"],
                    help="habillage seul avec transparence pour CapCut (qtrle par défaut, ou prores 4444)")
    rd.add_argument("--until", type=float, help="ne rendre que les N premières secondes")
    rd.add_argument("--no-tts", action="store_true")
    a = p.parse_args()
    return {"plan": cmd_plan, "check": cmd_check, "still": cmd_still, "render": cmd_render}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
