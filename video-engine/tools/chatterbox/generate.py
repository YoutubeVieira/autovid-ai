#!/usr/bin/env python3
"""Voix off locale avec Chatterbox Multilingual (clonage à partir d'un extrait de référence). SANS API, SANS QUOTA.
À lancer sur VOTRE machine (idéalement avec une carte graphique NVIDIA ou un Mac Apple Silicon) : ce script n'a pas pu être
testé dans la session de développement (les poids du modèle viennent de Hugging Face, bloqué là-bas).

Écrit un fichier par scène : public/projects/<projet>/voix-externe/<id de scène>.wav (mono, 16 bits).
Ensuite, dans le dépôt :  VOICE=fenrir-chatterbox node tools/tts.mjs <projet>

Usage : python3 tools/chatterbox/generate.py <projet> --ref voix/fenrir-reference.wav [--lang fr] [--only s01,s02]
Réglages utiles : --exagg 0.5 (expressivité, 0.3 à 0.8), --cfg 0.5 (plus bas = débit plus calme), --temp 0.8
"""
import argparse, json, os, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("projet")
ap.add_argument("--ref", required=True, help="extrait de voix de référence (10 à 40 s, propre, sans musique)")
ap.add_argument("--lang", default="fr")
ap.add_argument("--only", default="")
ap.add_argument("--exagg", type=float, default=0.5)
ap.add_argument("--cfg", type=float, default=0.5)
ap.add_argument("--temp", type=float, default=0.8)
a = ap.parse_args()

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
proj = json.load(open(os.path.join(root, "projects", a.projet + ".json"), encoding="utf-8"))
out = os.path.join(root, "public", "projects", a.projet, "voix-externe")
os.makedirs(out, exist_ok=True)
if not os.path.exists(a.ref):
    sys.exit("Extrait de référence introuvable : " + a.ref)

import torch, torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

device = "cuda" if torch.cuda.is_available() else ("mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu")
print("Appareil :", device, "(sur CPU, compter plusieurs fois la durée de l'audio)")
model = ChatterboxMultilingualTTS.from_pretrained(device=device)

def chunks(text, limit=260):
    """Phrases regroupées en morceaux courts : le modèle est plus stable sur des textes brefs."""
    parts, cur = [], ""
    for s in re.split(r"(?<=[.!?…])\s+", text.strip()):
        if cur and len(cur) + len(s) > limit: parts.append(cur); cur = s
        else: cur = (cur + " " + s).strip()
    if cur: parts.append(cur)
    return parts

only = [x for x in a.only.split(",") if x]
for s in proj["scenes"]:
    if only and s["id"] not in only: continue
    f = os.path.join(out, s["id"] + ".wav")
    if os.path.exists(f): print("=", s["id"], "(déjà produit)"); continue
    pieces = []
    for t in chunks(s["text"]):
        w = model.generate(t, language_id=a.lang, audio_prompt_path=a.ref, exaggeration=a.exagg, cfg_weight=a.cfg, temperature=a.temp)
        pieces.append(w.cpu()); pieces.append(torch.zeros(1, int(model.sr * 0.18)))
    wav = torch.cat(pieces[:-1], dim=1)
    ta.save(f, wav, model.sr, encoding="PCM_S", bits_per_sample=16)
    print("ok", s["id"], round(wav.shape[1] / model.sr, 1), "s")
print("Terminé. Étape suivante : VOICE=fenrir-chatterbox node tools/tts.mjs", a.projet)
