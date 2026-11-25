---
description: "Installer ou vérifier tout le projet vidéo sur ce PC"
---

Travaille dans le dossier `projet-video/` : toutes les commandes et chemins ci-dessous s'entendent depuis ce dossier.

1. `cd remotion && npm install` puis `npx tsc --noEmit`.
2. Effets sonores : `powershell -ExecutionPolicy Bypass -File outils/installer-earshot.ps1` (bash : `outils/installer-earshot.sh`).
3. Styles : `powershell -ExecutionPolicy Bypass -File outils/installer-styles.ps1` (demande avant : environ 200 Mo).
4. Transcription : `python -m pip install faster-whisper`.
5. Test : `npx remotion render AutoVidShort out/test.mp4 --props=./data/exemple-replica.json --scale=0.5` dans `remotion/`.
