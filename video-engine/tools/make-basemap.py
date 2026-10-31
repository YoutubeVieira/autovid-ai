#!/usr/bin/env python3
"""Fond de carte « satellite » : Natural Earth NE1_50M_SR_W (relief ombré naturel, domaine public),
reprojeté en Mercator sur l'Europe, aligné sur la projection de src/geo.ts (d3 geoMercator, échelle 1300),
puis assombri et désaturé pour le look documentaire. Écrit public/geo/basemap.jpg + basemap.json.
Usage : python3 tools/make-basemap.py [chemin/NE1_50M_SR_W.tif]   (télécharge si absent)"""
import io, json, math, os, sys, urllib.request, zipfile
import numpy as np
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://naturalearth.s3.amazonaws.com/50m_raster/NE1_50M_SR_W.zip"
LON0, LON1, LAT0, LAT1 = -25.0, 45.0, 27.0, 72.0   # même étendue que fetch-assets.mjs
S = 1300.0                                          # échelle de geo.ts
OUT_W = 3400

src = sys.argv[1] if len(sys.argv) > 1 else None
if not src or not os.path.exists(src):
    print("Téléchargement de Natural Earth (88 Mo)…")
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(URL, timeout=300).read()))
    name = [n for n in z.namelist() if n.endswith(".tif")][0]
    src = io.BytesIO(z.read(name))
im = Image.open(src).convert("RGB")
W0, H0 = im.size                                    # equirectangulaire : 360° x 180°

def merc_y(lat): return -S * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
x0, x1 = S * math.radians(LON0), S * math.radians(LON1)
y0, y1 = merc_y(LAT1), merc_y(LAT0)                # y0 en haut (lat 72)
OUT_H = round(OUT_W * (y1 - y0) / (x1 - x0))

# recadrage en longitude (linéaire), puis rééchantillonnage ligne par ligne en latitude (Mercator)
cx0, cx1 = round((LON0 + 180) / 360 * W0), round((LON1 + 180) / 360 * W0)
crop = np.asarray(im.crop((0, 0, W0, H0)))[:, cx0:cx1].astype(np.float32)
cols = np.asarray(Image.fromarray(crop.astype(np.uint8)).resize((OUT_W, H0), Image.BICUBIC)).astype(np.float32)
rows = np.arange(OUT_H)
y = y0 + (rows + 0.5) / OUT_H * (y1 - y0)
lat = np.degrees(2 * np.arctan(np.exp(-y / S)) - math.pi / 2)
sy = (90 - lat) / 180 * H0 - 0.5
i0 = np.clip(np.floor(sy).astype(int), 0, H0 - 2); fr = (sy - i0)[:, None, None]
out = cols[i0] * (1 - fr) + cols[i0 + 1] * fr

# étalonnage : plus sombre, désaturé, ombres bleu-vert
g = out.mean(axis=2, keepdims=True)
out = g + (out - g) * 0.82
out = out * np.array([0.46, 0.52, 0.55], dtype=np.float32)
out = 255 * np.power(np.clip(out / 255, 0, 1), 1.08)
img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
os.makedirs(os.path.join(root, "public/geo"), exist_ok=True)
img.save(os.path.join(root, "public/geo/basemap.jpg"), quality=86, optimize=True)
json.dump({"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0, "px": [OUT_W, OUT_H]}, open(os.path.join(root, "public/geo/basemap.json"), "w"))
print("basemap.jpg", img.size, round(os.path.getsize(os.path.join(root, "public/geo/basemap.jpg")) / 1e6, 2), "Mo")
