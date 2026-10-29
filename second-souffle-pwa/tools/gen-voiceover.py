#!/usr/bin/env python3
"""Génère docs/voiceover.json et docs/voiceover-manifest.csv à partir du contenu écrit dans
tools/voiceover_content.py, de docs/production-data.json (exercices V1) et des noms d'exercices de js/data.js.
Usage : python3 tools/gen-voiceover.py"""
import csv
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from voiceover_content import SESSION, EXTRA_EX, WELLNESS, MOTIV  # noqa: E402

LANGS = ["fr", "en", "pt"]
names = json.loads(subprocess.check_output(
    ["node", "-e", "require('./js/i18n.js');require('./js/data.js');console.log(JSON.stringify(SS.data.EX.map(e=>({id:e.id,n:e.n}))))"],
    cwd=root))
prod = {i["id"]: i for i in json.loads((root / "docs" / "production-data.json").read_text(encoding="utf-8"))["items"]}

cats = []
cats.append({"id": "seance", "title": "Séances", "desc": "Annonces pendant une séance : début, transitions, décomptes, fin.",
             "items": [{"id": i, "name": n, "t": t} for i, n, t in SESSION]})
cats.append({"id": "noms", "title": "Noms des exercices", "desc": "À dire avant chaque exercice, après « Prochain exercice ».",
             "items": [{"id": "n." + e["id"], "name": e["n"]["fr"], "t": e["n"]} for e in names]})
ex_items = []
for e in names:
    t = prod[e["id"]]["s"] if e["id"] in prod else EXTRA_EX[e["id"]]
    ex_items.append({"id": "x." + e["id"], "name": e["n"]["fr"], "t": t, "v1": e["id"] in prod})
cats.append({"id": "exercices", "title": "Exercices", "desc": "Consigne parlée de chacun des 28 exercices (19 pour la version 1).", "items": ex_items})
cats.append({"id": "bienetre", "title": "Bien-être", "desc": "Séances guidées avec pauses. Chaque phrase est un fichier audio ; la pause est du silence ajouté ensuite.",
             "items": [{"id": i, "name": n + " (" + d + ")", "segments": [{"t": s["t"], "pause": s["pause"]} for s in segs]} for i, n, d, segs in WELLNESS]})
for title, rows in MOTIV:
    cats.append({"id": "motiv-" + str(len(cats)), "title": "Motivation · " + title, "desc": "",
                 "items": [{"id": i, "name": i, "t": t} for i, t in rows]})

out = {"note": "Voix off de Second Souffle en français, anglais et portugais du Brésil. À relire (portugais : personne de langue maternelle brésilienne) et à faire valider pour les consignes d'exercice.",
       "langs": LANGS, "categories": cats}
(root / "docs" / "voiceover.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

def words(s): return len(s.split())
rows = []
for c in cats:
    for it in c["items"]:
        parts = it.get("segments")
        if parts:
            for n, s in enumerate(parts, 1):
                for l in LANGS:
                    rows.append([c["id"], it["id"] + ".%02d" % n, l, s["t"][l], s["pause"], round(words(s["t"][l]) / 2.5 + s["pause"], 1), "audio/%s/%s.%02d.mp3" % (l, it["id"], n)])
        else:
            for l in LANGS:
                rows.append([c["id"], it["id"], l, it["t"][l], 0, round(words(it["t"][l]) / 2.5, 1), "audio/%s/%s.mp3" % (l, it["id"])])
with open(root / "docs" / "voiceover-manifest.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["categorie", "id", "langue", "texte", "pause_apres_s", "duree_estimee_s", "fichier"])
    w.writerows(rows)
total = len(rows)
print("fichiers audio à produire :", total, "(", total // 3, "par langue )")
for l in LANGS:
    secs = sum(r[5] for r in rows if r[2] == l)
    print(l, "durée totale estimée : %.0f min" % (secs / 60))
