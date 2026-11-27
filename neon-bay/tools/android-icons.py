#!/usr/bin/env python3
"""Néon Bay : icônes et écran de démarrage de l'app Android (Capacitor).
Sources : icons/icon-512.png (icône classique) et icons/maskable-512.png (icône adaptative).
Écrit dans app-android/android/app/src/main/res/. Fond : #0D0B1A.
Usage : python3 tools/android-icons.py   (Pillow requis : pip install pillow)
Conseil : une source 1024x1024 donnerait des icônes plus nettes sur les grands écrans."""
import os
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RES = os.path.join(ROOT, 'app-android', 'android', 'app', 'src', 'main', 'res')
BG = (13, 11, 26, 255)  # #0D0B1A
icon = Image.open(os.path.join(ROOT, 'icons', 'icon-512.png')).convert('RGBA')
mask = Image.open(os.path.join(ROOT, 'icons', 'maskable-512.png')).convert('RGBA')
DENS = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}


def rounded(img, radius_ratio):
    m = Image.new('L', img.size, 0)
    r = int(img.size[0] * radius_ratio)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], r, fill=255)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.paste(img, (0, 0), m)
    return out


def circle(img):
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, img.size[0] - 1, img.size[1] - 1], fill=255)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.paste(img, (0, 0), m)
    return out


for d, k in DENS.items():
    folder = os.path.join(RES, 'mipmap-' + d)
    os.makedirs(folder, exist_ok=True)
    s = int(48 * k)  # icône classique (Android 7) : 48 dp
    rounded(icon.resize((s, s), Image.LANCZOS), .12).save(os.path.join(folder, 'ic_launcher.png'))
    circle(mask.resize((s, s), Image.LANCZOS)).save(os.path.join(folder, 'ic_launcher_round.png'))
    # icône adaptative : calque 108 dp ; l'image maskable occupe 88 dp pour que sa zone sûre (80 %) reste visible
    c = int(108 * k)
    fg = Image.new('RGBA', (c, c), BG)
    inner = int(88 * k)
    fg.paste(mask.resize((inner, inner), Image.LANCZOS), ((c - inner) // 2, (c - inner) // 2))
    fg.save(os.path.join(folder, 'ic_launcher_foreground.png'))

# couleur de fond de l'icône adaptative
with open(os.path.join(RES, 'values', 'ic_launcher_background.xml'), 'w', encoding='utf-8') as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#0D0B1A</color>\n</resources>\n')

# écrans de démarrage (Android 7 à 11 ; Android 12+ affiche l'icône sur le fond #0D0B1A, voir styles.xml)
for root, _, files in os.walk(RES):
    if 'splash.png' in files and os.path.basename(root).startswith('drawable'):
        p = os.path.join(root, 'splash.png')
        w, h = Image.open(p).size
        sp = Image.new('RGBA', (w, h), BG)
        s = int(min(w, h) * .45)
        sp.paste(icon.resize((s, s), Image.LANCZOS), ((w - s) // 2, (h - s) // 2))
        sp.convert('RGB').save(p)
print('Icônes et splash Android générés dans', os.path.normpath(RES))
