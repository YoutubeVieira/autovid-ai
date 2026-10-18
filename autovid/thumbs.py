"""Miniatures : ADN d'un lot de miniatures de référence + génération (16:9 YouTube et 9:16 couverture Shorts/Reels)."""
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from . import gfx

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def _load(path, max_side=640):
    img = np.array(Image.open(path).convert("RGB"))
    s = max_side / max(img.shape[:2])
    return cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img


def palette(img, k=5, iters=8):
    """Couleurs dominantes (k-moyennes), triées par importance."""
    px = img.reshape(-1, 3).astype(np.float32)[:: max(1, img.size // 3 // 20000)]
    rng = np.random.default_rng(0)
    c = px[rng.choice(len(px), k, replace=False)]
    for _ in range(iters):
        lab = np.argmin(((px[:, None] - c[None]) ** 2).sum(-1), axis=1)
        c = np.array([px[lab == j].mean(0) if (lab == j).any() else c[j] for j in range(k)])
    share = np.bincount(lab, minlength=k) / len(lab)
    order = np.argsort(-share)
    return [{"hex": "#%02x%02x%02x" % tuple(int(v) for v in c[j]), "part": round(float(share[j]), 3)} for j in order]


def thumb_dna(path):
    img = _load(path)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    edges = cv2.Canny(gray.astype(np.uint8), 80, 200).astype(np.float32) / 255
    h, w = gray.shape
    sal = edges * (0.5 + hsv[..., 1] / 255)            # saillance grossière : contours × saturation
    ys, xs = np.mgrid[0:h, 0:w]
    tot = sal.sum() or 1
    cx, cy = float((xs * sal).sum() / tot / w), float((ys * sal).sum() / tot / h)
    grid = [[round(float(edges[i * h // 3:(i + 1) * h // 3, j * w // 3:(j + 1) * w // 3].mean()), 3) for j in range(3)]
            for i in range(3)]
    # texte probable : zones de contours très denses et très contrastées (lettres)
    dense = cv2.blur(edges, (15, 15)) > 0.28
    return {
        "fichier": Path(path).name, "format": f"{w}x{h}", "ratio": round(w / h, 2),
        "luminosite": round(float(gray.mean() / 255), 3), "contraste": round(float(gray.std() / 255), 3),
        "saturation": round(float(hsv[..., 1].mean() / 255), 3),
        "chaleur": round(float((img[..., 0].astype(float) - img[..., 2]).mean() / 255), 3),
        "zones_sombres": round(float((gray < 50).mean()), 3), "hautes_lumieres": round(float((gray > 220).mean()), 3),
        "centre_sujet": [round(cx, 2), round(cy, 2)], "densite_grille_3x3": grid,
        "texte_probable": round(float(dense.mean()), 3), "palette": palette(img),
    }


def analyze_folder(folder, out=None):
    files = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in IMG_EXT)
    if not files:
        raise SystemExit(f"Aucune image dans {folder}")
    items = [thumb_dna(p) for p in files]
    keys = ("luminosite", "contraste", "saturation", "chaleur", "zones_sombres", "hautes_lumieres", "texte_probable")
    mean = {k: round(float(np.mean([i[k] for i in items])), 3) for k in keys}
    mean["centre_sujet"] = [round(float(np.mean([i["centre_sujet"][j] for i in items])), 2) for j in (0, 1)]
    style = {
        "ambiance": "sombre / cinématique" if mean["luminosite"] < 0.38 else "lumineuse",
        "temperature": "chaude" if mean["chaleur"] > 0.04 else ("froide" if mean["chaleur"] < -0.02 else "neutre"),
        "texte": "peu ou pas de texte" if mean["texte_probable"] < 0.02 else "texte présent",
        "sujet": "centré" if abs(mean["centre_sujet"][0] - 0.5) < 0.1 else
                 ("à gauche" if mean["centre_sujet"][0] < 0.5 else "à droite"),
    }
    dna = {"moyenne": mean, "style": style, "images": items}
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(dna, indent=2, ensure_ascii=False), encoding="utf-8")
    return dna


# --------------------------------------------------------------------------- génération

def _grade(img, warm=True, dark=0.0):
    """Étalonnage « cinéma » : ombres bleu-vert, hautes lumières orangées, contraste en S."""
    x = img.astype(np.float32) / 255
    lum = x.mean(axis=2, keepdims=True)
    shadow = np.array([0.0, 0.05, 0.10])
    high = np.array([0.10, 0.04, -0.06]) if warm else np.array([-0.04, 0.0, 0.08])
    x = x + shadow * (1 - lum) * 0.6 + high * lum * 0.6
    x = 0.5 + (x - 0.5) * 1.18
    x = x * (1 - dark)
    return np.clip(x * 255, 0, 255)


def _vignette(img, strength=0.55):
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xs - w / 2) / (w / 2)) ** 2 + ((ys - h / 2) / (h / 2)) ** 2)
    img *= (1 - strength * np.clip(d - 0.35, 0, 1) ** 1.5)[..., None]


def _rim(img, mask, color=gfx.GREEN, width=9):
    """Liseré lumineux autour du sujet (le détache du fond)."""
    m = (mask > 0.5).astype(np.uint8)
    edge = cv2.dilate(m, np.ones((width, width), np.uint8)) - m
    glow = cv2.GaussianBlur(edge.astype(np.float32), (0, 0), width)
    img += np.array(color, np.float32) * glow[..., None] * 1.6
    np.clip(img, 0, 255, out=img)


def make_thumbnails(frame, out_base, title, accent_word=None, mask=None, style="cinematique", accent=gfx.GREEN):
    """frame : image 9:16 RGB. Écrit <out_base>_youtube.jpg (1280x720) et <out_base>_cover.jpg (1080x1920)."""
    H9, W9 = frame.shape[:2]
    words = title.upper().split()
    if accent_word is None and words:
        accent_word = max(words, key=len)
    dark = 0.12 if style == "cinematique" else 0.0

    def text_block(canvas, cx, y, max_w, size):
        """Titre sur 2 lignes équilibrées ; la ligne qui contient le mot clé passe en jaune."""
        cut = min(range(1, len(words) + 1),
                  key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:])))) if len(words) > 2 else len(words)
        for ln in (words[:cut], words[cut:]):
            if not ln:
                continue
            col = gfx.YELLOW if accent_word in ln else gfx.WHITE
            spr = gfx.text_sprite(" ".join(ln), size, col, stroke=10, shadow=16, max_w=max_w)
            gfx.paste(canvas, spr, cx, y + spr.shape[0] / 2)
            y += spr.shape[0] * 0.82

    # couverture verticale
    cover = _grade(frame, dark=dark)
    if mask is not None:
        _rim(cover, cv2.resize(mask, (W9, H9)), accent)
    _vignette(cover)
    text_block(cover, W9 / 2, 160, W9 - 80, 150)
    Image.fromarray(cover.astype(np.uint8)).save(f"{out_base}_cover.jpg", quality=93)

    # miniature YouTube 16:9 : fond flouté élargi + sujet à droite + texte à gauche
    yt_w, yt_h = 1280, 720
    bg = cv2.resize(frame, (yt_w, int(yt_w * H9 / W9)))
    top = (bg.shape[0] - yt_h) // 2
    bg = cv2.GaussianBlur(bg[top: top + yt_h], (0, 0), 22).astype(np.float32) * 0.55
    sub_h = yt_h
    sub_w = int(W9 * sub_h / H9)
    subj = cv2.resize(frame, (sub_w, sub_h)).astype(np.float32)
    x0 = yt_w - sub_w - 40
    if mask is not None:
        m = cv2.resize(mask, (sub_w, sub_h))[..., None]
        bg[:, x0:x0 + sub_w] = bg[:, x0:x0 + sub_w] * (1 - m) + subj * m
    else:
        bg[:, x0:x0 + sub_w] = subj
    yt = _grade(bg, dark=dark)
    if mask is not None:
        full = np.zeros((yt_h, yt_w), np.float32)
        full[:, x0:x0 + sub_w] = cv2.resize(mask, (sub_w, sub_h))
        _rim(yt, full, accent, 7)
    _vignette(yt, 0.45)
    text_block(yt, (x0) / 2 + 20, 150, x0 - 40, 120)
    Image.fromarray(yt.astype(np.uint8)).save(f"{out_base}_youtube.jpg", quality=93)
    return f"{out_base}_youtube.jpg", f"{out_base}_cover.jpg"
