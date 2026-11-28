"""Importe de VRAIS enregistrements d'animaux dans le pack, en refusant les licences qui interdisent la monétisation.

Dossier d'entrée = fichiers audio + `licences.csv` (colonnes: fichier;espece;licence;auteur;source). Exemple:
    chien1.wav;chien;CC0;Jean Dupont;https://freesound.org/...
Licences acceptées: CC0, PD (domaine public), CC-BY (crédit obligatoire, ajouté à CREDITS.md), CC-BY-SA (crédit + partage identique, signalé).
Refusées: CC-BY-NC, CC-BY-NC-SA, ND, inconnue ou absente (interdit en vidéo monétisée).
Traitement: mono 44,1 kHz, rognage des silences, pic normalisé à -3 dB, fondu court.
    python3 importer_sons.py <dossier_entree> [--out packs/animals]"""
import argparse
import csv
import json
import os
import re
import subprocess

OK = {"CC0": "CC0", "PD": "PD", "CC-BY": "CC-BY", "CC-BY-SA": "CC-BY-SA"}


def norm_lic(s):
    t = re.sub(r"[\s_]+", "-", (s or "").strip().upper()).replace("CC-BY-4.0", "CC-BY").replace("CC-BY-3.0", "CC-BY")
    t = t.replace("CC0-1.0", "CC0").replace("PUBLIC-DOMAIN", "PD").replace("DOMAINE-PUBLIC", "PD")
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entree")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    rows = list(csv.DictReader(open(os.path.join(a.entree, "licences.csv"), encoding="utf-8"), delimiter=";"))
    os.makedirs(os.path.join(a.out, "sons"), exist_ok=True)
    man, credits, refuses = [], [], []
    for r in rows:
        lic = norm_lic(r.get("licence"))
        src = os.path.join(a.entree, r["fichier"])
        if lic not in OK:
            refuses.append((r["fichier"], f"licence « {r.get('licence') or 'inconnue'} » non utilisable en vidéo monétisée"))
            continue
        if not os.path.exists(src):
            refuses.append((r["fichier"], "fichier absent"))
            continue
        espece = re.sub(r"[^a-z0-9]+", "_", r["espece"].lower()).strip("_")
        n = sum(1 for m in man if m["espece"] == espece) + 1
        dst = os.path.join(a.out, "sons", f"{espece}_{n:02d}.wav")
        af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
              "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.1,areverse,afade=t=in:d=0.01,afade=t=out:d=0.05,"
              "loudnorm=I=-18:TP=-3:LRA=11")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-ac", "1", "-ar", "44100", "-af", af, dst], check=True)
        man.append({"file": f"sons/{os.path.basename(dst)}", "espece": espece, "licence": lic, "auteur": r.get("auteur", ""), "source": r.get("source", "")})
        if lic in ("CC-BY", "CC-BY-SA"):
            credits.append(f"- {espece} : « {r['fichier']} » par {r.get('auteur', '?')} ({lic}) {r.get('source', '')}")
    json.dump({"sons": man}, open(os.path.join(a.out, "manifest.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    with open(os.path.join(a.out, "CREDITS.md"), "w", encoding="utf-8") as f:
        f.write("# Crédits des sons d'animaux\n\nÀ copier dans la description de la vidéo quand ces sons sont utilisés.\n\n" + ("\n".join(credits) or "Aucun crédit requis (CC0 / domaine public)."))
    print(f"{len(man)} sons importés, {len(refuses)} refusés")
    for f_, why in refuses:
        print("  refusé:", f_, "-", why)


if __name__ == "__main__":
    main()
