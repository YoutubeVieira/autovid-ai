"""Voix clonée avec Chatterbox Multilingual de Resemble AI (licence MIT, vente autorisée).
Chaque fichier produit contient un filigrane inaudible (PerTh) qui signale une voix générée.
Usage : python chatterbox_tts.py texte.txt sortie.wav <langue fr|pt|en> echantillon.wav
Installation : pip install chatterbox-tts   (GPU NVIDIA conseillé ; sur CPU c'est lent)."""
import re
import sys

import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

texte_path, sortie, langue, echantillon = sys.argv[1:5]
texte = open(texte_path, encoding="utf-8").read().strip()
device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
model = ChatterboxMultilingualTTS.from_pretrained(device=device)

# Phrase par phrase : la qualité baisse sur les textes longs.
phrases = [p for p in re.split(r"(?<=[.!?…])\s+", texte) if p.strip()]
morceaux = []
for i, phrase in enumerate(phrases):
    wav = model.generate(phrase, language_id=langue, audio_prompt_path=echantillon if i == 0 else None)
    morceaux.append(wav)
    morceaux.append(torch.zeros(1, int(model.sr * 0.2)))
ta.save(sortie, torch.cat(morceaux, dim=1), model.sr)
