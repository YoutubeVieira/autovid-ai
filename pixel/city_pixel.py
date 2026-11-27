"""Moteur de scenes pixel-art 'ville vue de dessus' (PIL + ffmpeg), resolution logique 180x320, agrandie x4 -> 720x1280.
Tout est dessine par code (aucune image tierce). Utilise la police pixel du depot (packs/fonts).
Usage via un module d'episode (voir caragua_fr.py)."""
import math
import os
import random
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

LW, LH, SCALE = 180, 320, 4
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "packs", "fonts", "PressStart2P-Regular.ttf")
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def text(d, xy, s, size=8, fill=(255, 255, 255), anchor="la", outline=None):
    d.fontmode = "1"
    if outline:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            d.text((xy[0] + dx, xy[1] + dy), s, font=font(size), fill=outline, anchor=anchor)
    d.text(xy, s, font=font(size), fill=fill, anchor=anchor)


def box(d, x0, y0, x1, y1, fill, border=None):
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=border)


# ------------------------------------------------------------------ monde
WW, WH = 220, 1180
RIVER_X = 168
C = dict(grass=(20, 44, 30), road=(38, 40, 46), line=(95, 95, 100), side=(128, 118, 100), sand=(176, 154, 108),
         water=(14, 26, 62), wall=(176, 166, 140), win=(26, 34, 62), door=(78, 50, 34),
         roofs=[(150, 60, 40), (184, 94, 50), (112, 112, 118), (108, 70, 50)], tree=(24, 66, 38),
         plaza=(104, 96, 84), court=(36, 84, 150), gray=(128, 132, 138))


def build_world(seed=5):
    rnd = random.Random(seed)
    img = Image.new("RGB", (WW, WH), C["grass"])
    d = ImageDraw.Draw(img)
    # fleuve + plage + avenue
    box(d, RIVER_X, 0, WW, WH, C["water"])
    box(d, 154, 0, RIVER_X - 1, WH, C["sand"])
    box(d, 138, 0, 153, WH, C["road"])
    box(d, 152, 0, 153, WH, C["side"])
    for y in range(0, WH, 12):
        d.line([(145, y), (145, y + 5)], fill=C["line"])
    # rues horizontales
    for y in range(150, 1180, 40):
        box(d, 0, y, 137, y + 7, C["road"])
        for x in range(2, 136, 10):
            d.line([(x, y + 3), (x + 4, y + 3)], fill=C["line"])
    windows = []

    def house(x, y, w=22, h=14, roof=None, tag=None):
        rc = roof or rnd.choice(C["roofs"])
        box(d, x + 1, y + 1, x + w, y + h, (14, 22, 20))                      # ombre
        box(d, x, y, x + w - 1, y + h // 2, rc)
        box(d, x, y + h // 2, x + w - 1, y + h // 2, tuple(int(c * .7) for c in rc))
        box(d, x, y + h // 2 + 1, x + w - 1, y + h - 1, C["wall"])
        for k in range(2):
            wx = x + 3 + k * (w // 2 - 1)
            box(d, wx, y + h // 2 + 3, wx + 2, y + h // 2 + 5, C["win"])
            windows.append((wx + 1, y + h // 2 + 4))
        box(d, x + w // 2 - 1, y + h - 4, x + w // 2 + 1, y + h - 1, C["door"])

    # quartier de maisons (zone B) et quartier final (zone G)
    for y in list(range(158, 560, 40)) + list(range(930, 1170, 40)):
        for x in (10, 42, 74, 106):
            if rnd.random() < 0.93:
                house(x + rnd.randint(-1, 2), y + 10 + rnd.randint(-1, 1))
                if rnd.random() < 0.5:
                    house(x + 1, y + 28 - 1 if y + 28 < WH else y, 22, 10)
            if rnd.random() < 0.5:
                tx, ty = x + rnd.randint(2, 20), y + rnd.randint(8, 30)
                d.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=C["tree"])
    # zone A: hopital, courts, parking
    box(d, 70, 28, 120, 62, C["gray"])
    for yy in range(30, 62, 4):
        d.line([(70, yy), (120, yy)], fill=(112, 116, 122))
    box(d, 92, 38, 98, 52, (190, 40, 40))
    box(d, 86, 43, 104, 47, (190, 40, 40))
    box(d, 10, 36, 56, 66, C["court"])
    d.rectangle([12, 38, 54, 64], outline=(200, 210, 220))
    d.line([(33, 38), (33, 64)], fill=(200, 210, 220))
    box(d, 70, 70, 128, 112, (82, 82, 86))
    for x in range(74, 126, 8):
        d.line([(x, 74), (x, 108)], fill=(150, 150, 150))
    for k in range(10):
        tx, ty = rnd.randint(8, 130), rnd.randint(8, 24)
        d.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=C["tree"])
    # zone C: ecole + place
    house(12, 470, 40, 24, (206, 110, 40))
    box(d, 60, 472, 96, 494, C["court"])
    d.rectangle([62, 474, 94, 492], outline=(200, 210, 220))
    box(d, 8, 520, 136, 572, C["plaza"])
    for tx in (18, 40, 100, 124, 20, 118):
        ty = 528 + rnd.randint(0, 36)
        d.ellipse([tx - 4, ty - 4, tx + 4, ty + 4], fill=C["tree"])
    d.ellipse([64, 540, 80, 556], fill=(40, 90, 160))
    # zone D: plage, tour de sauvetage, ponton
    box(d, 124, 560, 168, 700, C["sand"])
    box(d, 142, 596, 150, 608, (210, 60, 50))
    box(d, 142, 596, 150, 600, (240, 190, 60))
    box(d, 150, 648, 200, 655, (112, 80, 50))
    for x in range(152, 200, 4):
        d.line([(x, 648), (x, 655)], fill=(86, 60, 38))
    box(d, 178, 660, 188, 664, (225, 225, 230))
    # zone E: immeubles blancs
    for x0, x1 in ((18, 74), (84, 134)):
        box(d, x0, 706, x1, 744, (190, 192, 198))
        for x in range(x0 + 2, x1, 4):
            d.line([(x, 708), (x, 742)], fill=(150, 152, 160))
    # zone F: prefecture
    box(d, 36, 828, 132, 880, C["gray"])
    for yy in range(830, 880, 4):
        d.line([(36, yy), (132, yy)], fill=(104, 108, 116))
    box(d, 62, 882, 106, 890, (190, 190, 190))
    box(d, 80, 870, 88, 880, (60, 40, 30))
    box(d, 138, 826, 139, 860, (150, 150, 150))
    box(d, 140, 826, 150, 832, (60, 170, 70))
    # grain
    px = np.asarray(img).astype(np.int16)
    noise = np.random.default_rng(seed).integers(-5, 6, size=(WH, WW, 1))
    px = np.clip(px + noise, 0, 255)
    # teinte nocturne sur le monde (hors sprites/lumieres dessines ensuite)
    px = np.clip(px * np.array([0.80, 0.86, 1.05]), 0, 255).astype(np.uint8)
    return Image.fromarray(px, "RGB"), windows


def lamps(world, spacing=24):
    d = ImageDraw.Draw(world, "RGBA")
    pts = []
    for y in range(10, WH, spacing):
        pts += [(135, y), (156, y)]
    for x, y in pts:
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 210, 110, 40))
        d.point((x, y), fill=(255, 225, 140, 255))


def truck(d, x, y, cab_right=True, big=1):
    s = big
    box(d, x, y, x + 12 * s, y + 6 * s, (62, 150, 72), (20, 70, 30))
    box(d, x + 12 * s, y + 1 * s, x + 17 * s, y + 6 * s, (235, 235, 240), (140, 140, 150))
    box(d, x + 14 * s, y + 2 * s, x + 16 * s, y + 3 * s, (110, 170, 230))
    for wx in (2, 10, 14):
        box(d, x + wx * s, y + 6 * s, x + (wx + 2) * s, y + 7 * s, (10, 10, 12))


def person(d, x, y, shirt=(240, 130, 40), s=1):
    box(d, x, y, x + 3 * s, y + 3 * s, (240, 200, 160))
    box(d, x, y + 4 * s, x + 3 * s, y + 7 * s, shirt)
    box(d, x, y + 8 * s, x + 3 * s, y + 10 * s, (40, 60, 130))
    box(d, x, y - 1 * s, x + 3 * s, y, (70, 40, 20))


def ease(t):
    return t * t * (3 - 2 * t)


class Renderer:
    def __init__(self, fps=30):
        self.fps = fps
        self.world, self.windows = build_world()
        lamps(self.world)
        rnd = random.Random(2)
        self.lit_order = sorted(range(len(self.windows)), key=lambda i: rnd.random())
        self.room = self._room()

    # ------------- salle du conseil
    def _room(self):
        im = Image.new("RGB", (LW, LH), (82, 52, 36))
        d = ImageDraw.Draw(im)
        for y in range(0, LH, 10):
            d.line([(0, y), (LW, y)], fill=(66, 42, 30))
        for x in range(0, LW, 22):
            d.line([(x, 0), (x, LH)], fill=(72, 46, 33))
        box(d, 0, 0, LW, 50, (96, 58, 46))
        for y in range(0, 50, 6):
            d.line([(0, y), (LW, y)], fill=(78, 46, 38))
        box(d, 48, 56, 132, 180, (140, 26, 36), (214, 170, 52))
        d.rectangle([50, 58, 130, 178], outline=(214, 170, 52))
        pts = [(26 + k * 32, 200) for k in range(5)] + [(16 + k * 12, 82 + k * 28) for k in range(5)] + \
              [(150 - k * 12, 82 + k * 28) for k in range(5)]
        for x, y in pts:
            box(d, x, y, x + 14, y + 9, (126, 80, 44), (60, 36, 20))
            box(d, x + 3, y + 3, x + 10, y + 4, (50, 30, 18))
        return im

    # ------------- rendu d'une vue
    def view(self, cx, cy, zoom, t, extra=None):
        layer = self.world.copy()
        d = ImageDraw.Draw(layer, "RGBA")
        # fleuve qui scintille
        for k in range(55):
            x = RIVER_X + 4 + (k * 37 + int(t * 6)) % (WW - RIVER_X - 6)
            y = (k * 61) % WH
            d.line([(x, y), (x + 3, y)], fill=(44, 70, 130, 255))
        if extra:
            extra(d, layer)
        vw, vh = LW / zoom, LH / zoom
        x0 = int(round(min(max(cx - vw / 2, 0), WW - vw)))
        y0 = int(round(min(max(cy - vh / 2, 0), WH - vh)))
        crop = layer.crop((x0, y0, x0 + int(round(vw)), y0 + int(round(vh))))
        crop = crop.resize((LW, LH), Image.NEAREST)
        return crop, (x0, y0)

    def to_screen(self, org, zoom, wx, wy):
        return int((wx - org[0]) * zoom), int((wy - org[1]) * zoom)

    # ------------- ecriture video
    def write(self, out_path, nframes, frame_fn):
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{LW * SCALE}x{LH * SCALE}", "-r", str(self.fps), "-i", "-", "-c:v", "libx264", "-crf", "12",
               "-pix_fmt", "yuv420p", str(out_path)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(nframes):
            im = frame_fn(i / self.fps).convert("RGB").resize((LW * SCALE, LH * SCALE), Image.NEAREST)
            p.stdin.write(im.tobytes())
        p.stdin.close()
        p.wait()
