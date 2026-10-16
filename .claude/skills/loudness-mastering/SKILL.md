---
name: loudness-mastering
description: Normalise le son d'une video courte a -14 LUFS et mixe une musique avec ducking sous la voix.
---
# loudness-mastering

Les deux videos de reference mesurent -14,1 LUFS integres: c'est la cible du preset (`audio.lufs`, crete `audio.true_peak` -1,5 dBTP).
Le rendu fait un loudnorm en 2 passes (mesure puis correction lineaire). Musique: `--music fichier`, boucle automatiquement, `audio.music_gain` (0,18), `sidechaincompress` la baisse quand la voix parle.
Verifier: `python3 -m autoeditor analyze final.mp4` -> `loudness.input_i` doit etre -14 +/- 1. Si la voix est noyee par la musique, baisser `music_gain` a 0,12.
