import colorsys, glob, json, sys
import numpy as np
from PIL import Image

U = "/root/.claude/uploads/96eec817-88f3-53c2-b829-ab3907c7fbe1/"
FILES = ["ee819a3e", "15313ea3", "88975f1f", "d0f9af96", "e2552c9f", "965d9e5c", "7e93aef4"]
tiles = []
for k in FILES:
    f = glob.glob(U + k + "*")[0]
    im = np.asarray(Image.open(f).convert("RGB"))
    H, W, _ = im.shape
    # grille de miniatures: 3 colonnes de 360 px, lignes de ~480 px entre y=400 et y=2270
    for row in range(0, 4):
        y0 = 400 + row * 480
        if y0 + 400 > 2270:
            break
        for c in range(3):
            t = im[y0:y0 + 380, c * 360 + 8:(c + 1) * 360 - 8]   # on retire le bas (compteur de vues)
            if t.shape[0] > 300:
                tiles.append(t)
print(len(tiles), "miniatures analysees")
px = np.concatenate([t[::5, ::5].reshape(-1, 3) for t in tiles]).astype(np.float32)
print(px.shape[0], "pixels")

rng = np.random.default_rng(1)
K = 16
cent = px[rng.choice(len(px), K, replace=False)]
for _ in range(25):
    d = ((px[:, None, :] - cent[None]) ** 2).sum(-1)
    lab = d.argmin(1)
    for k in range(K):
        m = lab == k
        if m.any():
            cent[k] = px[m].mean(0)
share = np.bincount(lab, minlength=K) / len(px)
rows = []
for k in np.argsort(-share):
    r, g, b = cent[k] / 255
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    rows.append({"hex": "#%02X%02X%02X" % tuple(int(x) for x in cent[k]), "part_%": round(float(share[k]) * 100, 1),
                 "teinte_deg": int(round(h * 360)), "saturation": float(round(s, 2)), "valeur": float(round(v, 2))})
for r in rows:
    print(r)

# stats globales par miniature: luminosite moyenne (jour/nuit), saturation
lums, sats = [], []
for t in tiles:
    a = t[::6, ::6].reshape(-1, 3) / 255.0
    lums.append(float((0.2126 * a[:, 0] + 0.7152 * a[:, 1] + 0.0722 * a[:, 2]).mean()))
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in a[::7]])
    sats.append(float(hsv[:, 1].mean()))
lums, sats = np.array(lums), np.array(sats)
print("luminosite moyenne: %.2f | miniatures sombres (<0.30): %d%% | claires (>0.45): %d%%" % (lums.mean(), 100 * (lums < 0.30).mean(), 100 * (lums > 0.45).mean()))
print("saturation moyenne: %.2f" % sats.mean())
json.dump({"clusters": rows, "tiles": len(tiles), "lum_mean": float(lums.mean()), "sat_mean": float(sats.mean()),
           "dark_share": float((lums < 0.30).mean())}, open(sys.argv[1], "w"), indent=2)
