"""Primitives graphiques image par image : textes (sprites Pillow), étiquettes, superposition, lueurs."""
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = Path(__file__).parent / "fonts"
ANTON = str(FONTS / "Anton-Regular.ttf")
MARKER = str(FONTS / "PermanentMarker-Regular.ttf")

GREEN = (57, 255, 20)
ORANGE = (255, 120, 0)
YELLOW = (255, 230, 0)
WHITE = (255, 255, 255)
RED = (255, 40, 60)


@lru_cache(maxsize=64)
def _font(path, size):
    return ImageFont.truetype(path, size)


@lru_cache(maxsize=512)
def text_sprite(text, size=96, color=WHITE, font=ANTON, stroke=6, shadow=10, max_w=1000):
    """Texte blanc épais à contour noir + ombre floutée, en RGBA (numpy). Réduit si plus large que max_w."""
    f = _font(font, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    while r - l > max_w and size > 20:
        size = int(size * 0.92)
        f = _font(font, size)
        l, t, r, b = f.getbbox(text, stroke_width=stroke)
    pad = shadow * 2 + stroke
    img = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 4, pad - t + 7), text, font=f, fill=(0, 0, 0, 200),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(shadow / 2)))
    ImageDraw.Draw(img).text((pad - l, pad - t), text, font=f, fill=color + (255,), stroke_width=stroke,
                             stroke_fill=(0, 0, 0, 255))
    return np.array(img)


@lru_cache(maxsize=128)
def label_sprite(title, sub, accent=GREEN):
    """Étiquette anatomie : bandeau sombre, barre de couleur, nom du muscle + rôle."""
    ft, fs = _font(ANTON, 46), _font(ANTON, 30)
    wt = int(ft.getlength(title))
    ws = int(fs.getlength(sub))
    w, h = max(wt, ws) + 58, 112
    img = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((6, 8, w + 6, h + 8), 16, fill=(0, 0, 0, 120))
    d.rounded_rectangle((0, 0, w, h), 16, fill=(12, 12, 16, 215))
    d.rounded_rectangle((0, 0, 12, h), 6, fill=accent + (255,))
    d.text((30, 6), title, font=ft, fill=accent + (255,))
    d.text((30, 64), sub.upper(), font=fs, fill=(235, 235, 235, 255))
    return np.array(img)


def paste(dst, sprite, cx, cy, scale=1.0, alpha=1.0):
    """Colle un sprite RGBA centré en (cx, cy) sur une image RGB float32 (0–255)."""
    if alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.01:
        sprite = cv2.resize(sprite, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = sprite.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    H, W = dst.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x0c, y0c = max(0, x0), max(0, y0)
    x1c, y1c = min(W, x0 + w), min(H, y0 + h)
    if x1c <= x0c or y1c <= y0c:
        return
    s = sprite[sy0: sy0 + (y1c - y0c), sx0: sx0 + (x1c - x0c)].astype(np.float32)
    a = s[..., 3:4] / 255.0 * alpha
    region = dst[y0c:y1c, x0c:x1c]
    region *= 1 - a
    region += s[..., :3] * a


def pop(t, dur=0.18, over=1.25):
    """Échelle d'apparition « pop » : grossit puis se stabilise à 1."""
    if t <= 0:
        return 0.0
    if t >= dur:
        return 1.0
    x = t / dur
    return over * np.sin(x * np.pi / 2) if x < 0.6 else 1 + (over - 1) * (1 - x) / 0.4


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def glow_fill(frame, mask, color, alpha=0.6, glow=0.55, box=None):
    """Colore une zone (masque 0–1) avec une lueur néon. `box` = (x0, y0, x1, y1) limite le calcul."""
    if box is not None:
        h, w = mask.shape
        x0, y0, x1, y1 = max(int(box[0]), 0), max(int(box[1]), 0), min(int(box[2]), w), min(int(box[3]), h)
        if x1 - x0 < 8 or y1 - y0 < 8:
            return
        glow_fill(frame[y0:y1, x0:x1], mask[y0:y1, x0:x1], color, alpha, glow)
        return
    m = mask[..., None]
    col = np.array(color, np.float32)
    frame *= 1 - alpha * m
    frame += col * alpha * m
    h, w = mask.shape                      # lueur calculée au quart de la résolution : 16x moins cher
    small = cv2.resize(mask, (max(w // 4, 1), max(h // 4, 1)), interpolation=cv2.INTER_AREA)
    g = cv2.resize(cv2.GaussianBlur(small, (0, 0), 3.5), (w, h), interpolation=cv2.INTER_LINEAR)[..., None]
    frame += col * g * glow
    np.clip(frame, 0, 255, out=frame)


def line(frame, a, b, color, thick, alpha=1.0):
    if alpha >= 0.99:
        cv2.line(frame, tuple(map(int, a)), tuple(map(int, b)), color, int(thick), cv2.LINE_AA)
        return
    over = frame.copy()
    cv2.line(over, tuple(map(int, a)), tuple(map(int, b)), color, int(thick), cv2.LINE_AA)
    cv2.addWeighted(over, alpha, frame, 1 - alpha, 0, dst=frame)


def ring(frame, c, r, color, thick=5):
    cv2.circle(frame, tuple(map(int, c)), int(r), (0, 0, 0), int(thick) + 4, cv2.LINE_AA)
    cv2.circle(frame, tuple(map(int, c)), int(r), color, int(thick), cv2.LINE_AA)


def dot(frame, c, r, color):
    cv2.circle(frame, tuple(map(int, c)), int(r) + 3, (0, 0, 0), -1, cv2.LINE_AA)
    cv2.circle(frame, tuple(map(int, c)), int(r), color, -1, cv2.LINE_AA)
