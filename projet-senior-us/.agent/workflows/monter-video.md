---
description: Monter une séance en vidéo 1080p avec habillage discret, voix off et sous-titres
---

1. Vérifie la séance : `python3 autovideo.py check sessions/<slug>.json`.
2. Génère les images de contrôle : `python3 autovideo.py still sessions/<slug>.json --at 1`, puis `--at 3`, `--at 6`, au milieu d'un exercice et d'un repos, et 3 s avant la fin. Ouvre chaque image et vérifie lisibilité et visibilité du coach (voir `AGENTS.md`).
3. Corrige si besoin (`text_tone`, `text_side`, clip du coach) et refais l'image concernée.
4. Rends : `python3 autovideo.py render sessions/<slug>.json`.
5. Contrôle la sortie avec `ffprobe out/<slug>/<slug>.mp4` (1920×1080, 30 i/s, durée attendue).
6. Donne à l'utilisateur les chemins de la vidéo, de `youtube/description.txt` et de `youtube/captions.en.srt`.
