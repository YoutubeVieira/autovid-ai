"""Vérificateur de phonétique française: réécoute chaque phrase de la voix avec Whisper et la compare au texte attendu.

    python3 verifier_phonetique.py <script.txt> <dossier_voix> --asr-model packs/voices/models/sherpa-onnx-whisper-base [--seuil 0.2] [--ajouter]

Pour chaque phrase: taux d'erreur de mots, mots mal compris (attendu -> entendu). Les mots douteux sont proposés pour prononciation.json
(--ajouter écrit une entrée vide à compléter: respelling, ex. "habitants": "abitan"). Whisper-base se trompe parfois tout seul sur les noms
propres/mots rares: un mot signalé est à ÉCOUTER, pas forcément faux. Écoute toujours les phrases >= seuil."""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "editor"))
from autoeditor import asr  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("script")
ap.add_argument("voix")
ap.add_argument("--asr-model", required=True)
ap.add_argument("--seuil", type=float, default=0.2)
ap.add_argument("--ajouter", action="store_true")
a = ap.parse_args()
cues = json.load(open(os.path.join(a.voix, "voice.json"), encoding="utf-8"))["cues"]
wav = os.path.join(a.voix, "voice.wav")
pj = os.path.join(HERE, "prononciation.json")
bad, rows, suspects = 0, [], {}
for c in cues:
    heard = asr.transcribe(a.asr_model, wav, start=max(0, c["start"] - 0.1), end=c["end"] + 0.15)
    wer, diffs = asr.compare(c["text"], heard)
    rows.append((wer, c["text"], heard, diffs))
    for d in diffs:
        if d["attendu"] and len(d["attendu"].split()) == 1:
            suspects[d["attendu"]] = d["entendu"]
    bad += wer >= a.seuil
for wer, txt, heard, diffs in rows:
    print(f"{'OK ' if wer < a.seuil else 'A ÉCOUTER'} {wer:4.0%} | attendu: {txt}\n        entendu: {heard}")
    for d in diffs:
        print(f"        - {d['attendu']!r} -> {d['entendu']!r}")
print(f"\n{len(rows) - bad}/{len(rows)} phrases claires. Mots douteux: {', '.join(suspects) or 'aucun'}")
if a.ajouter and suspects:
    d = json.load(open(pj, encoding="utf-8"))
    for w in suspects:
        d.setdefault(w, "")
    json.dump(d, open(pj, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("ajoutés (vides, à compléter) dans prononciation.json")
sys.exit(1 if bad else 0)
