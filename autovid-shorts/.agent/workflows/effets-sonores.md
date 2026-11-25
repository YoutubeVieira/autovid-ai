---
description: "Ajouter, régler ou remplacer les effets sonores d'une vidéo"
---

1. Suis `.claude/agents/sound-designer.md`.
2. Sons automatiques : `remotion/src/sfx.ts` ; réglages par vidéo dans `remotion/data/<slug>.json` (`sfx`, `sfxExtra`).
3. Nouveaux sons : `.venv-earshot/Scripts/earshot make "<description>" -o remotion/public/sfx/<nom>.mp3` (après `outils/installer-earshot.ps1`), ou `python outils/chercher-sons.py "<mots>" --liste` (Openverse).
4. Vérifie par mesure (`silencedetect`) que chaque son tombe sur son apparition à l'écran.
