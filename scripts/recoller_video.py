"""Recolle une vidéo envoyée en morceaux depuis la plateforme Studio Jacobina.

  python3 scripts/recoller_video.py projet_lu.json dossier_des_morceaux/ -o video.mp4
`projet_lu.json` : le document du projet (ArtifactData get/list avec out_dir). Les morceaux sont les assets
`source.morceaux[].id`, téléchargés avec Artifact read (path = id) dans `dossier_des_morceaux/`.
"""
import argparse
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("doc")
ap.add_argument("dossier")
ap.add_argument("-o", "--out", required=True)
a = ap.parse_args()
doc = json.loads(Path(a.doc).read_text(encoding="utf-8"))
doc = doc.get("data", doc)
src = doc["source"]
parts = src.get("morceaux") or [{"id": src["id"]}]
files = []
for p in parts:
    hits = sorted(Path(a.dossier).rglob(f"{p['id']}*"))
    if not hits:
        raise SystemExit(f"morceau manquant : {p['id']} (le télécharger avec Artifact read, path = cet id)")
    files.append(hits[0])
with open(a.out, "wb") as out:
    for f in files:
        out.write(f.read_bytes())
size = Path(a.out).stat().st_size
want = src.get("octets")
if want and size != want:
    raise SystemExit(f"taille recollée {size} ≠ taille d'origine {want} : un morceau est incomplet")
print(f"{a.out} : {len(files)} morceau(x), {size / 1048576:.1f} Mo")
