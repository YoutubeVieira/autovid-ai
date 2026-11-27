---
name: correcteur-audio-video
description: Détecte et répare les défauts d'un audio ou d'une vidéo (volume, saturation, silences, bruit de fond, noir au début/fin, format, cadence, désynchro, faststart) et contrôle la diction d'une voix avec Whisper.
---
# correcteur-audio-video
```bash
cd editor
python3 -m autoeditor check video.mp4 --preset monde_tiktok --duree 25 30 [--json rapport.json]
python3 -m autoeditor fix video.mp4 -o video_ok.mp4 --preset monde_tiktok [--silent-audio]
python3 -m autoeditor check voix.wav --expect "texte attendu" --asr-model <sherpa-onnx-whisper-small>   # diction
python3 -m autoeditor fix voix.wav -o voix_ok.wav
```
Défauts détectés: volume hors cible (LUFS), crête vraie, écrêtage, composante continue, bruit de fond, silences (début, fin, longs), format ≠ cible, cadence, pixel format ≠ yuv420p, cadence variable, index en fin de fichier, noir de début/fin, image figée, désynchronisation audio/vidéo, absence d'audio, durée hors cible, mots mal compris par Whisper.
Réparations automatiques: adeclip/adeclick, passe-haut 70 Hz, débruitage afftdn, rognage des silences/noirs, loudnorm 2 passes + limiteur, mise au format (recadrage 9:16), yuv420p, cadence fixe, aresample async, `+faststart`. Modèle Whisper: `https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2` (base = plus léger mais moins fiable sur les phrases courtes).
Limite: aucune détection ne remplace l'écoute; une voix peut être « comprise » par Whisper et sonner mal.
