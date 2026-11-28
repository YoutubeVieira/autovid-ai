---
name: auto-edit
description: Monte automatiquement un rush video en video courte verticale (9:16) avec coupe des silences, jump-cuts, sous-titres, musique et mastering -14 LUFS. A utiliser des qu'on demande de monter, couper, sous-titrer ou "editer" une video.
---
# auto-edit

Pipeline: `editor/autoeditor` (ffmpeg + Python standard).

1. Verifier `ffmpeg -version`. Travailler dans un dossier de sortie a part (`out/`), jamais ecraser le rush.
2. Lancer:
   ```bash
   cd editor
   python3 -m autoeditor run <rush.mp4> --out-dir <out> [--srt <fichier.srt>] [--hook "<texte>"] [--music <fichier>]
   ```
3. Lire la sortie: le dernier etat doit etre `RESULTAT: VALIDE`. Sinon ouvrir `qa.json`, corriger le reglage concerne dans `presets/` et relancer (3 essais max).
4. Regarder au moins 3 images du resultat avant de rendre la main (voir l'agent `qa-reviewer`).

Sans `--srt` et sans `faster-whisper`, la video est montee sans sous-titres: le dire a l'utilisateur.
Pour un autre style, copier `presets/shortform_9x16.json` sous un nouveau nom et passer `--preset`.
Tests: `python3 -m unittest discover -s editor/tests -v`.
