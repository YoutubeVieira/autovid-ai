"""Prépare le document « projet » de la plateforme (Studio Jacobina) à partir d'un rendu.

  python3 scripts/plateforme_doc.py sortie.projet.json --nom "Roda" --url /_blob/<id> --duree 27.2 \
      [--ancien doc.json] -o doc.json
Avec --ancien (le document lu dans la plateforme), la nouvelle version s'ajoute aux précédentes.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("projet")
ap.add_argument("--nom", required=True)
ap.add_argument("--url", required=True)
ap.add_argument("--duree", type=float, default=0)
ap.add_argument("--note", default="")
ap.add_argument("--ancien")
ap.add_argument("-o", "--out", required=True)
a = ap.parse_args()
projet = json.loads(Path(a.projet).read_text(encoding="utf-8"))
old = json.loads(Path(a.ancien).read_text(encoding="utf-8")) if a.ancien else {}
old = old.get("data", old)
versions = old.get("versions", [])
now = datetime.now()
versions.append({"n": len(versions) + 1, "url": a.url, "date": now.strftime("%d/%m %H:%M"), "duree": a.duree,
                 "note": a.note})
doc = {"nom": a.nom, "statut": "pret", "cree": old.get("cree", now.isoformat()), "modifie": now.isoformat(),
       "versions": versions, "projet": projet}
Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
print(a.out)
