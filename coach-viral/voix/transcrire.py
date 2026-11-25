"""Transcription gratuite (faster-whisper, licence MIT).
Usage : python transcrire.py audio.wav [taille_modele] [--mots]
  sans --mots : écrit le texte prononcé
  avec --mots : écrit du JSON [{"mot", "debut", "fin"}] pour les sous-titres mot à mot
Installation : pip install faster-whisper   (le modèle « small » tient sur CPU)."""
import json
import sys

# Sous Windows, la sortie vers un autre programme n'est pas en UTF-8 par defaut : les accents casseraient le JSON.
sys.stdout.reconfigure(encoding="utf-8")

from faster_whisper import WhisperModel

args = [a for a in sys.argv[1:] if not a.startswith("--")]
mots = "--mots" in sys.argv
audio = args[0]
taille = args[1] if len(args) > 1 else "small"
model = WhisperModel(taille, device="auto", compute_type="int8")
segments, info = model.transcribe(audio, vad_filter=True, word_timestamps=mots)
if mots:
    sortie = []
    for s in segments:
        for w in s.words or []:
            sortie.append({"mot": w.word.strip(), "debut": round(w.start, 3), "fin": round(w.end, 3)})
    print(json.dumps(sortie, ensure_ascii=False))
else:
    print(" ".join(s.text.strip() for s in segments))
