"""Vidéo longue YouTube 16:9 avec chapitres, construite à partir du short analysé.

Structure (rétention YouTube : promesse tout de suite, plan annoncé, meilleur moment vers les 2/3, chapitres) :
  0:00 Intro : l'accroche du short + « au programme » (liste des chapitres)
  Chapitre n : carte titre → le mouvement EN VRAI à vitesse normale → l'analyse au ralenti avec sa fiche
               (placement, muscles, risque, astuce)
  Fin : carte « abonne-toi » + prochaine vidéo
Écrit aussi `<sortie>.chapitres.txt` (à coller dans la description YouTube).
"""
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import gfx, sfx
from .media import FPS, info, run
from .render import match_loudness

LW, LH = 1920, 1080
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
BODY_FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf", gfx.ANTON]


def _body(size):
    for p in BODY_FONTS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.truetype(gfx.ANTON, size)


def _wrap(draw, text, font, width):
    lines, cur = [], ""
    for w in str(text).split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def order_chapters(analyses):
    """Meilleur moment (score max) placé vers les 2/3 de la vidéo, les autres dans l'ordre du combat."""
    if len(analyses) < 3:
        return list(analyses)
    best = max(analyses, key=lambda a: a["score"])
    rest = [a for a in analyses if a is not best]
    pos = round(2 / 3 * (len(analyses) - 1))
    return rest[:pos] + [best] + rest[pos:]


def group_by_technique(analyses, max_per=3):
    """Un chapitre par technique : les passages du même mouvement sont montrés à la suite (comparaison)."""
    groups = {}
    for a in sorted(analyses, key=lambda a: a["src_t"]):
        g = groups.setdefault(a["nom"], {**a, "items": []})
        if len(g["items"]) < max_per:
            g["items"].append(a)
        g["score"] = max(g["score"], a["score"])
    return list(groups.values())


def chapters_text(marks):
    """Chapitres au format YouTube (le premier à 0:00, au moins 3, 10 s minimum chacun)."""
    return "\n".join(f"{int(t // 60)}:{int(t % 60):02d} {title}" for t, title in marks)


# --------------------------------------------------------------------------- panneaux (PNG transparents)

def fiche_png(a, path, accent, chapter=None):
    """Fiche à droite de l'analyse : nom, placement, muscles, risque, astuce."""
    img = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, x1, y = 960, 1840, 120
    d.rounded_rectangle((x0 - 40, 70, x1 + 30, LH - 70), 28, fill=(10, 12, 10, 205))
    d.rectangle((x0 - 40, 70, x0 - 28, LH - 70), fill=accent + (255,))
    if chapter:
        d.text((x0, y), f"CHAPITRE {chapter}", font=_body(30), fill=(190, 196, 180, 255))
        y += 46
    d.text((x0, y), a["nom"], font=ImageFont.truetype(gfx.ANTON, 92), fill=(255, 255, 255, 255))
    y += 120
    if a.get("cle"):
        d.text((x0, y), a["cle"], font=ImageFont.truetype(gfx.ANTON, 50), fill=gfx.YELLOW + (255,))
        y += 80
    body = _body(30)
    if a.get("placement"):
        d.text((x0, y), "PLACEMENT", font=_body(26), fill=accent + (255,))
        y += 38
        for line in _wrap(d, a["placement"], body, x1 - x0)[:3]:
            d.text((x0, y), line, font=body, fill=(240, 240, 235, 255))
            y += 40
        y += 18
    if a.get("muscles"):
        d.text((x0, y), "MUSCLES", font=_body(26), fill=accent + (255,))
        y += 38
        for nom, role in a["muscles"][:3]:
            d.text((x0, y), nom, font=ImageFont.truetype(gfx.ANTON, 40), fill=(255, 255, 255, 255))
            d.text((x0 + 300, y + 8), role, font=_body(28), fill=(200, 205, 195, 255))
            y += 52
        y += 14
    if a.get("risque"):
        zone, conseil = (a["risque"] + ["", ""])[:2]
        d.text((x0, y), "ATTENTION : " + zone, font=_body(30), fill=gfx.RED + (255,))
        y += 42
        for line in _wrap(d, conseil, _body(28), x1 - x0)[:2]:
            d.text((x0, y), line, font=_body(28), fill=(240, 240, 235, 255))
            y += 38
        y += 14
    if a.get("tip") and y < LH - 170:
        d.text((x0, y), "ASTUCE", font=_body(26), fill=gfx.YELLOW + (255,))
        y += 38
        for line in _wrap(d, a["tip"], _body(28), x1 - x0)[:2]:
            d.text((x0, y), line, font=_body(28), fill=(255, 255, 255, 255))
            y += 38
    img.save(path)


def programme_png(chapters, best_idx, path, accent):
    img = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0 = 960
    d.rounded_rectangle((x0 - 40, 70, 1870, LH - 70), 28, fill=(10, 12, 10, 205))
    d.rectangle((x0 - 40, 70, x0 - 28, LH - 70), fill=accent + (255,))
    d.text((x0, 120), "AU PROGRAMME", font=ImageFont.truetype(gfx.ANTON, 84), fill=(255, 255, 255, 255))
    y = 250
    for i, a in enumerate(chapters, 1):
        col = gfx.YELLOW if i - 1 == best_idx else (240, 240, 235)
        d.text((x0, y), f"{i}.", font=ImageFont.truetype(gfx.ANTON, 54), fill=accent + (255,))
        d.text((x0 + 80, y), a["nom"], font=ImageFont.truetype(gfx.ANTON, 54), fill=col + (255,))
        y += 82
        if y > LH - 200:
            break
    d.text((x0, LH - 170), f"LE PLUS IMPORTANT : CHAPITRE {best_idx + 1}", font=_body(32), fill=gfx.YELLOW + (255,))
    img.save(path)


def card_png(path, kicker, title, sub, accent, handle=""):
    img = Image.new("RGB", (LW, LH), (14, 15, 12))
    d = ImageDraw.Draw(img)
    for x in range(0, LW, 80):                  # grille discrète (comme l'intro 3D)
        d.line((x, 0, x, LH), fill=(26, 30, 24))
    for yy in range(0, LH, 80):
        d.line((0, yy, LW, yy), fill=(26, 30, 24))
    d.rectangle((0, LH // 2 + 150, LW, LH // 2 + 162), fill=accent)
    f_k, f_t, f_s = _body(40), ImageFont.truetype(gfx.ANTON, 190), ImageFont.truetype(gfx.ANTON, 72)

    def center(text, font, y, fill):
        w = d.textlength(text, font=font)
        d.text(((LW - w) / 2, y), text, font=font, fill=fill, stroke_width=4, stroke_fill=(0, 0, 0))
    if kicker:
        center(kicker, f_k, 210, (190, 196, 180))
    center(title, f_t, 290, (255, 255, 255))
    if sub:
        center(sub, f_s, LH // 2 + 190, gfx.YELLOW)
    if handle:
        center(handle, _body(34), LH - 110, (170, 175, 165))
    img.save(path)


def lower_third_png(path, text, accent):
    img = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(gfx.ANTON, 54)
    w = d.textlength(text, font=f)
    d.rounded_rectangle((80, LH - 190, 80 + w + 70, LH - 100), 14, fill=(10, 12, 10, 215))
    d.rectangle((80, LH - 190, 92, LH - 100), fill=accent + (255,))
    d.text((120, LH - 180), text, font=f, fill=(255, 255, 255, 255))
    img.save(path)


# --------------------------------------------------------------------------- morceaux vidéo

def _card_audio(path, dur, hits=(0.0,)):
    sr = sfx.SR
    n = int(dur * sr)
    mix = sfx.music_phonk(dur + 0.1)[:n] * 0.35
    for t in hits:
        for name, g in (("low_whoosh", 0.8), ("sub_boom", 0.8)):
            x = sfx.LIB[name]() * g
            i = int((t + (0.25 if name == "sub_boom" else 0)) * sr)
            x = x[: max(n - i, 0)]
            mix[i: i + len(x)] += x
    sfx.write_wav(path, mix / (np.abs(mix).max() or 1) * 0.8)


def piece_card(png, dur, out, work):
    wav = work / (Path(out).stem + ".wav")
    _card_audio(wav, dur)
    frames = int(dur * FPS)
    run(["ffmpeg", "-y", "-v", "error", "-i", png, "-i", wav, "-filter_complex",
         f"[0:v]scale={LW * 2}:{LH * 2},zoompan=z='1+0.06*on/{frames}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
         f":d={frames}:s={LW}x{LH}:fps={FPS},setsar=1[v]", "-map", "[v]", "-map", "1:a", "-frames:v", str(frames),
         "-t", f"{dur:.3f}", *ENC, out])


def piece_vertical(clip, t0, t1, overlay_png, out):
    """Morceau du short 9:16 à gauche, fond flouté, panneau (PNG) par-dessus."""
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", clip, "-i", overlay_png,
         "-filter_complex",
         f"[0:v]split[a][b];[a]scale={LW}:{LH}:force_original_aspect_ratio=increase,crop={LW}:{LH},gblur=sigma=30,"
         f"eq=brightness=-0.22:saturation=0.8[bg];[b]scale=-2:{LH}[fg];[bg][fg]overlay=150:0[m];[m][1:v]overlay=0:0,"
         f"fps={FPS},setsar=1,format=yuv420p[v]", "-map", "[v]", "-map", "0:a?", *ENC, out])


def piece_original(src, t0, t1, overlay_png, out):
    """Le mouvement en vrai, à vitesse normale, en 16:9 (fond flouté si la source est verticale)."""
    i = info(src)
    vf = (f"[0:v]split[a][b];[a]scale={LW}:{LH}:force_original_aspect_ratio=increase,crop={LW}:{LH},gblur=sigma=30,"
          f"eq=brightness=-0.2[bg];[b]scale={LW}:{LH}:force_original_aspect_ratio=decrease[fg];"
          f"[bg][fg]overlay=(W-w)/2:(H-h)/2[m]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{max(t0, 0):.3f}", "-to", f"{t1:.3f}", "-i", src, "-i", overlay_png]
    if i["has_audio"]:
        amap = ["-map", "0:a", "-af", "highpass=f=70,afftdn=nf=-28"]
    else:
        cmd += ["-f", "lavfi", "-t", f"{t1 - t0:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        amap = ["-map", "2:a"]
    run(cmd + ["-filter_complex", vf + f";[m][1:v]overlay=0:0,fps={FPS},setsar=1,format=yuv420p[v]", "-map", "[v]",
               *amap, *ENC, out])


def _dur(path):
    return float(info(str(path))["duration"])


def long_video(src, short, segments, out, workdir, handle="", accent=gfx.GREEN, next_title=None):
    """src : vidéo d'origine ; short : le short analysé (combat) ; segments : son .segments.json."""
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    out = Path(out).resolve()
    seg = json.loads(Path(segments).read_text(encoding="utf-8"))
    chapters = order_chapters(group_by_technique(seg["analyses"]))
    next_title = next_title or ("L'ESQUIVA" if seg.get("discipline") == "capoeira" else "LA DÉFENSE")
    if not chapters:
        raise SystemExit("aucune analyse dans le short : pas de vidéo longue possible")
    best = max(range(len(chapters)), key=lambda j: chapters[j]["score"])
    src_dur = _dur(src)
    pieces, marks, t = [], [], 0.0

    def add(path, title=None):
        nonlocal t
        if title:
            marks.append((t, title))
        pieces.append(path)
        t += _dur(path)

    print(f"vidéo longue : {len(chapters)} chapitres (le meilleur en n° {best + 1})")
    programme_png(chapters, best, work / "programme.png", accent)
    piece_vertical(short, 0, max(seg["intro_fin"], 3.0), work / "programme.png", str(work / "p_intro.mp4"))
    add(work / "p_intro.mp4", "Intro")
    if _dur(work / "p_intro.mp4") < 10:          # chapitre YouTube : 10 s minimum → plan large de la vidéo en vrai
        lower_third_png(work / "lt_intro.png", "EN VRAI", accent)
        a0 = chapters[0]["src_t"]
        piece_original(src, max(a0 - 6, 0), min(max(a0 - 6, 0) + 10 - _dur(work / "p_intro.mp4") + 0.5, src_dur),
                       work / "lt_intro.png", str(work / "p_intro2.mp4"))
        add(work / "p_intro2.mp4")
    for i, a in enumerate(chapters, 1):
        card_png(work / f"card{i}.png", f"CHAPITRE {i}", a["nom"], a.get("cle", ""), accent, handle)
        piece_card(str(work / f"card{i}.png"), 2.4, str(work / f"p{i}_card.mp4"), work)
        add(work / f"p{i}_card.mp4", f"{i}. {a['nom'].title()}" + (f" : {a['cle'].lower()}" if a.get("cle") else ""))
        fiche_png(a, work / f"fiche{i}.png", accent, i)
        for j, it in enumerate(a["items"], 1):
            tag = f" · PASSAGE {j}/{len(a['items'])}" if len(a["items"]) > 1 else ""
            lower_third_png(work / f"lt{i}_{j}.png", f"EN VRAI · {a['nom']}{tag}", accent)
            piece_original(src, it["src_t"] - 3.0, min(it["src_t"] + 2.0, src_dur), work / f"lt{i}_{j}.png",
                           str(work / f"p{i}_{j}_vrai.mp4"))
            add(work / f"p{i}_{j}_vrai.mp4")
            piece_vertical(short, max(it["debut"] - 0.3, 0), it["fin"], work / f"fiche{i}.png",
                           str(work / f"p{i}_{j}_analyse.mp4"))
            add(work / f"p{i}_{j}_analyse.mp4")
    card_png(work / "fin.png", "MERCI D'AVOIR REGARDÉ", "ABONNE-TOI", "PROCHAINE VIDÉO : " + next_title, accent, handle)
    piece_card(str(work / "fin.png"), 4.0, str(work / "p_fin.mp4"), work)
    add(work / "p_fin.mp4")                    # pas de chapitre : YouTube exige 10 s minimum par chapitre

    lst = work / "pieces.txt"
    lst.write_text("".join(f"file '{Path(p).resolve()}'\n" for p in pieces))
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, *ENC,
         "-af", "loudnorm=I=-14:TP=-1:LRA=9", "-movflags", "+faststart", work / "long_brut.mp4"])
    match_loudness(str(work / "long_brut.mp4"), str(out), -14)
    chap = chapters_text(marks)
    Path(out.with_suffix(".chapitres.txt")).write_text(chap + "\n", encoding="utf-8")
    print(chap)
    return str(out), marks
