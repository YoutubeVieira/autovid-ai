"""Voix off gratuite avec Kokoro-82M (poids Apache-2.0, vente autorisée). Tourne sur CPU.
Usage : python kokoro_tts.py texte.txt sortie.wav <langue f|p|a> <voix> [vitesse]
Installation : pip install kokoro soundfile  (+ espeak-ng installé sur la machine)."""
import sys

import numpy as np
import soundfile as sf
from kokoro import KPipeline

texte_path, sortie, lang, voix = sys.argv[1:5]
vitesse = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
texte = open(texte_path, encoding="utf-8").read().strip()

pipeline = KPipeline(lang_code=lang)
morceaux = []
# Une phrase par morceau : Kokoro limite chaque passage à 510 phonèmes.
for resultat in pipeline(texte, voice=voix, speed=vitesse, split_pattern=r"(?<=[.!?…])\s+"):
    if resultat.audio is not None:
        morceaux.append(resultat.audio.numpy())
        morceaux.append(np.zeros(int(24000 * 0.18), dtype=np.float32))
if not morceaux:
    sys.exit("Aucun son produit.")
sf.write(sortie, np.concatenate(morceaux), 24000)
