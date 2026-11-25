#!/usr/bin/env python3
"""Cherche et télécharge des effets sonores libres sur Openverse (api.openverse.org).

À lancer sur votre PC : l'API n'est pas joignable depuis une session Claude dans le cloud.
Même fichier dans le dépôt autovid-senior (outils/).

Exemples :
  python3 outils/chercher-sons.py "soft chime" --liste
  python3 outils/chercher-sons.py "soft chime" --choix 2 --nom repos --dossier entrees/exemple-50s/sons
  python3 outils/chercher-sons.py whoosh --choix 1 --nom whoosh --dossier remotion/public/sfx --licence cc0,by

Pour chaque son téléchargé, un fichier <nom>.txt contient le crédit (titre, auteur, licence, lien) :
il est repris automatiquement dans la description YouTube. Par défaut seule la licence CC0
(aucun crédit obligatoire) est cherchée ; avec « by », le crédit est OBLIGATOIRE.
Les licences « nc » (pas d'usage commercial) sont refusées : une chaîne monétisée est un usage commercial.
"""
import argparse
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.openverse.org/v1/audio/"
COMMERCIAL_OK = {"cc0", "pdm", "by", "by-sa"}


def search(query, licences, max_seconds, n):
    params = {"q": query, "license": ",".join(licences), "page_size": str(min(50, n * 3)),
              "category": "sound_effect"}
    for attempt in (params, {k: v for k, v in params.items() if k != "category"}):
        url = API + "?" + urllib.parse.urlencode(attempt)
        req = urllib.request.Request(url, headers={"User-Agent": "autovid-shorts/1.0 (chercher-sons)"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                results = json.load(r).get("results", [])
        except urllib.error.HTTPError as e:
            if e.code == 400 and "category" in attempt:
                continue  # filtre de catégorie refusé : on réessaie sans
            sys.exit(f"Openverse a répondu {e.code} : {e.reason}")
        except urllib.error.URLError as e:
            sys.exit(f"Openverse injoignable ({e.reason}). Ce script doit tourner sur votre PC.")
        out = [r for r in results
               if r.get("license") in COMMERCIAL_OK and r.get("url")
               and (not r.get("duration") or r["duration"] <= max_seconds * 1000)]
        return out[:n]
    return []


def credit(r):
    lic = f'CC {r["license"].upper()} {r.get("license_version") or ""}'.strip()
    if r["license"] in ("cc0", "pdm"):
        lic = "CC0 / public domain"
    # En anglais : ce texte est recopié tel quel dans la description YouTube.
    return f'"{r.get("title") or "Untitled"}" by {r.get("creator") or "unknown"} ({lic}) — {r.get("foreign_landing_url") or r["url"]}'


def download(r, folder, name, max_seconds):
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / f".{name}.download"
    req = urllib.request.Request(r["url"], headers={"User-Agent": "autovid-shorts/1.0 (chercher-sons)"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(tmp, "wb") as f:
        shutil.copyfileobj(resp, f)
    out = folder / f"{name}.mp3"
    # Normalisé : stéréo 44,1 kHz, coupé à max_seconds, fondu de sortie pour éviter un clic.
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-t", str(max_seconds),
                    "-af", f"afade=t=out:st={max(0, max_seconds - 0.3)}:d=0.3,loudnorm=I=-16:TP=-2",
                    "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-q:a", "4", str(out)], check=True)
    tmp.unlink()
    out.with_suffix(".txt").write_text(credit(r) + "\n", encoding="utf-8")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("recherche", help='mots-clés en anglais, ex. "soft whoosh", "gentle bell"')
    p.add_argument("--licence", default="cc0", help="licences acceptées : cc0 (défaut), by, by-sa, pdm, séparées par des virgules")
    p.add_argument("--max", type=float, default=4.0, help="durée maximale en secondes (défaut 4)")
    p.add_argument("--n", type=int, default=8, help="nombre de résultats affichés")
    p.add_argument("--liste", action="store_true", help="afficher les résultats sans rien télécharger")
    p.add_argument("--choix", type=int, help="numéro du résultat à télécharger")
    p.add_argument("--nom", help="nom du fichier sans extension (ex. repos, whoosh)")
    p.add_argument("--dossier", default="sons", help="dossier de destination")
    a = p.parse_args()

    licences = [l.strip() for l in a.licence.split(",") if l.strip()]
    bad = [l for l in licences if l not in COMMERCIAL_OK]
    if bad:
        sys.exit(f"Licence(s) refusée(s) : {', '.join(bad)} (pas d'usage commercial ou inconnue)")
    results = search(a.recherche, licences, a.max, a.n)
    if not results:
        sys.exit("Aucun résultat : essayez d'autres mots-clés en anglais, ou --licence cc0,by")
    for i, r in enumerate(results, 1):
        dur = f'{r["duration"] / 1000:.1f} s' if r.get("duration") else "? s"
        print(f'{i:2d}. {dur:>6}  {r["license"]:<6} {(r.get("title") or "")[:50]:<50}  {r.get("foreign_landing_url") or ""}')
    if a.liste or not a.choix:
        print("\nÉcoutez sur la page indiquée, puis relancez avec --choix N --nom <nom>.")
        return
    if not a.nom:
        sys.exit("Indiquez --nom (ex. --nom repos)")
    r = results[a.choix - 1]
    out = download(r, Path(a.dossier), a.nom, a.max)
    print(f"\n✔ {out}\n  crédit : {out.with_suffix('.txt')}")
    if r["license"] not in ("cc0", "pdm"):
        print("  ⚠ licence avec attribution : le crédit doit apparaître dans la description de la vidéo.")


if __name__ == "__main__":
    main()
