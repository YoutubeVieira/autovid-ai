"""Version francaise de la video 'ville pixel' (35 s, 720x1280): scenes pixel-art + events.json pour le monteur autonome.
Les temps des scenes suivent la voix (voice.json de packs/voices/tts.py).

Usage: python caragua_fr.py --voice <dossier voice.json> --out <dossier>
Sortie: source.mp4 (sans son, sans HUD ni sous-titres), events.json"""
import argparse
import json
import math
import os

from PIL import Image, ImageDraw

import city_pixel as cp
from city_pixel import LH, LW, box, person, text, truck

ap = argparse.ArgumentParser()
ap.add_argument("--voice", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--fps", type=int, default=30)
args = ap.parse_args()
cues = json.load(open(os.path.join(args.voice, "voice.json"), encoding="utf-8"))["cues"]
T = lambda i: cues[i]["start"]
E = lambda i: cues[i]["end"]
END = E(14) + 0.25                      # fin du contenu; le carton de fin est ajoute par le monteur

# ---------------------------------------------------------------- plan de camera: (debut, fin, cam_debut, cam_fin)
d78 = (E(7) - T(7)) / 5                  # les 5 metiers: un plan chacun
JOBS = [("PROFESSEUR", (40, 484, 1.7), (30, 470)), ("MÉDECIN", (96, 52, 1.5), (80, 24)),
        ("ÉBOUEUR", (96, 296, 1.4), (100, 292)), ("SAUVETEUR", (148, 604, 1.7), (140, 590)),
        ("PÊCHEUR", (170, 652, 1.7), (160, 636))]
SHOTS = [
    (0, T(1), (90, 40, 1.0), (90, 85, 1.0)),
    (T(1), T(2), (88, 100, 1.0), (88, 125, 1.0)),
    (T(2), T(4), (80, 190, 1.0), (80, 300, 1.0)),
    (T(4), T(7), (50, 268, 2.0), (52, 274, 2.2)),
] + [(T(7) + k * d78, T(7) + (k + 1) * d78, j[1], (j[1][0], j[1][1] + 4, j[1][2])) for k, j in enumerate(JOBS)] + [
    (E(7), T(9), (80, 742, 1.0), (80, 722, 1.0)),
    (T(9), T(11), "room", "room"),
    (T(11), T(12), (84, 858, 1.6), (84, 850, 1.6)),
    (T(12), T(12) + 0.55 * (E(12) - T(12)), (90, 200, 1.0), (90, 232, 1.0)),
    (T(12) + 0.55 * (E(12) - T(12)), T(13), (112, 846, 1.25), (112, 842, 1.25)),
    (T(13), END, (60, 302, 1.8), (62, 308, 1.8)),
]
R = cp.Renderer(args.fps)
lit_n = len(R.windows)


def cam_at(t):
    for t0, t1, a, b in SHOTS:
        if t0 <= t < t1 or (t >= END and t1 == END):
            if a == "room":
                return "room", (t - t0) / (t1 - t0)
            u = cp.ease((t - t0) / max(1e-6, t1 - t0))
            return tuple(a[k] + (b[k] - a[k]) * u for k in range(3)), (t - t0) / (t1 - t0)
    return (90, 40, 1.0), 0


def label(d, org, zoom, wx, wy, s, color=(255, 255, 255), fill=(10, 14, 26)):
    x, y = R.to_screen(org, zoom, wx, wy)
    w = len(s) * 8 + 8
    x = max(2, min(LW - w - 2, x - w // 2))
    y = max(40, min(LH - 20, y))
    box(d, x, y, x + w, y + 12, fill, (230, 230, 235))
    text(d, (x + 5, y + 2), s, 8, color)


def frame(t):
    cam, u = cam_at(t)
    # ---- salle du conseil (scene interieure)
    if cam == "room":
        im = R.room.copy()
        dd = ImageDraw.Draw(im)
        z = 1.0 + 0.05 * u
        im = im.crop((int(LW * (1 - 1 / z) / 2), int(LH * (1 - 1 / z) / 2), LW - int(LW * (1 - 1 / z) / 2), LH - int(LH * (1 - 1 / z) / 2))).resize((LW, LH), Image.NEAREST)
        d = ImageDraw.Draw(im)
        if t >= T(9) + 0.5:
            box(d, 68, 44, 112, 88, (250, 202, 44), (20, 20, 20))
            text(d, (90, 66), "15", 20, (20, 20, 20), "mm")
            text(d, (90, 98), "SIÈGES VIDES", 8, (255, 255, 255), "mm", (0, 0, 0))
        return im

    def extra(dw, layer):
        # fenetres allumees (progressif pendant les plans 3 et 4, puis partiel)
        prog = 0.0 if t < T(2) + 0.8 else min(1.0, (t - T(2) - 0.8) / (T(4) - T(2)))
        n = int(lit_n * (0.5 * prog if t < T(4) else 0.5 + 0.0))
        for i in R.lit_order[:n]:
            x, y = R.windows[i]
            dw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 205, 90, 45))
            dw.point((x, y), fill=(255, 220, 120, 255))
            dw.point((x - 1, y), fill=(255, 220, 120, 255))
        # camions
        truck(dw, int((t * 16) % 150) - 20, 163 + 40 * int(t // 9 % 4))
        truck(dw, 200 - int((t * 12) % 190), 886 if t > T(11) else 603 + 40, big=1)
        # bateau + pecheur
        dw.rectangle([178, 660 + int(math.sin(t * 2) * 1), 188, 664 + int(math.sin(t * 2) * 1)], fill=(225, 225, 230))
        person(dw, 168, 637, (90, 140, 220))
        # TOI
        if T(5) + 0.4 <= t < END:
            px = 20 + min(1.0, (t - T(5) - 0.4) / 1.6) * 38 if t < T(7) else 58
            person(dw, int(px), 281 if t < T(9) else 313)
            box(dw, int(px) + 5, 284 if t < T(9) else 316, int(px) + 8, 291 if t < T(9) else 323, (50, 150, 70))

    im, org = R.view(cam[0], cam[1], cam[2], t, extra)
    d = ImageDraw.Draw(im)
    z = cam[2]
    # ---- bloc jaune "0" (accroche)
    if 0.5 <= t < T(2):
        box(d, 70, 104, 110, 144, (250, 202, 44), (20, 20, 20))
        text(d, (90, 124), "0", 24, (20, 20, 20), "mm")
    # ---- cadre "abonne = habitant"
    if T(4) + 0.2 <= t < T(4) + 1.9:
        box(d, 8, 54, 172, 70, (60, 200, 110), (10, 60, 30))
        text(d, (90, 62), "ABONNÉ = HABITANT ✓".replace("✓", "OK"), 8, (10, 40, 20), "mm")
    # ---- champ de commentaire qui se tape
    if T(5) <= t < E(6):
        box(d, 6, 50, 174, 84, (14, 18, 30), (220, 220, 225))
        text(d, (12, 56), "PRÉNOM + MÉTIER", 8, (150, 160, 180))
        full = "ANA, PROFESSEURE"
        p = min(1.0, max(0.0, (t - T(5) - 0.25) / max(0.4, E(5) - T(5) - 0.5)))
        s = full[:int(len(full) * p)] + ("_" if int(t * 3) % 2 == 0 else "")
        text(d, (12, 68), s, 8, (255, 255, 255))
    # ---- etiquette "TOI" / nom
    if T(5) + 0.6 <= t < END and cam != "room":
        nm = "TOI" if t < E(5) or t >= T(13) else "ANA"
        if T(4) <= t < T(7) or t >= T(13):
            label(d, org, z, 60, 276 if t < T(9) else 308, nm, (255, 230, 120))
    # ---- postes a pourvoir (plans metiers)
    for k, (nm, camj, anchor) in enumerate(JOBS):
        if T(7) + k * d78 <= t < T(7) + (k + 1) * d78 + 0.05:
            label(d, org, z, anchor[0] + 18, anchor[1], f"POSTE : {nm}", (255, 255, 255))
    # ---- mairie fermee
    if T(11) <= t < T(12):
        if t >= T(11) + 0.25:
            box(d, 24, 90, 156, 120, (205, 40, 45), (255, 255, 255))
            text(d, (90, 105), "FERMÉE X", 12, (255, 255, 255), "mm")
        x, y = R.to_screen(org, z, 84, 872)
        box(d, x - 7, y - 3, x + 7, y + 9, (240, 190, 40), (40, 30, 10))
        d.rectangle([x - 4, y - 10, x + 4, y - 3], outline=(60, 60, 70))
    # ---- 0 / 100 + election
    if T(12) <= t < T(12) + 0.55 * (E(12) - T(12)):
        box(d, 36, 104, 144, 136, (250, 202, 44), (20, 20, 20))
        text(d, (90, 120), "0 / 100", 14, (20, 20, 20), "mm")
        text(d, (90, 148), "HABITANTS", 8, (255, 255, 255), "mm", (0, 0, 0))
    elif T(12) + 0.55 * (E(12) - T(12)) <= t < T(13):
        label(d, org, z, 96, 826, "ÉLECTION DU MAIRE", (255, 214, 70))
    return im


nframes = int(END * args.fps) + 1
os.makedirs(args.out, exist_ok=True)
R.write(os.path.join(args.out, "source.mp4"), nframes, frame)

# ---------------------------------------------------------------- evenements pour le monteur
ev = [{"t": 0.0, "type": "hud_sub", "text": "0 HABITANTS · 0 EMPLOIS"},
      {"t": round(T(2) + 0.8, 2), "type": "badge", "text": "+1 HABITANT", "color": "yellow"},
      {"t": round(T(3) + 0.35, 2), "type": "badge", "text": "+1 EMPLOI", "color": "green"},
      {"t": round(T(5), 2), "type": "sfx", "name": "pop"},
      {"t": round(T(4) + 0.2, 2), "type": "sfx", "name": "coin"},
      {"t": round(T(9) + 0.5, 2), "type": "sfx", "name": "stamp"},
      {"t": round(T(9), 2), "type": "hud_sub", "text": "CONSEIL : 0/15 SIÈGES"},
      {"t": round(T(11), 2), "type": "hud_sub", "text": "MAIRIE : FERMÉE"},
      {"t": round(T(11) + 0.25, 2), "type": "sfx", "name": "error_buzz"},
      {"t": round(T(12), 2), "type": "hud_sub", "text": "ÉLECTION DU MAIRE À 100"},
      {"t": round(T(12), 2), "type": "sfx", "name": "ding"},
      {"t": round(T(13), 2), "type": "hud_sub", "text": "0 HABITANTS"}]
for a, b, *_ in SHOTS[1:]:
    ev.append({"t": round(a, 2), "type": "cut"})
ev.sort(key=lambda e: e["t"])
json.dump({"fps": args.fps, "content_duration": round(END, 2), "events": ev}, open(os.path.join(args.out, "events.json"), "w"),
          indent=2, ensure_ascii=False)
print("ok", nframes, "images,", round(END, 1), "s ->", args.out)
