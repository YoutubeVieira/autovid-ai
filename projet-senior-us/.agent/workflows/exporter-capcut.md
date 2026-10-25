---
description: Préparer le dossier à déposer dans CapCut pour retoucher la séance
---

1. Rends avec la couche transparente : `python3 autovideo.py render sessions/<slug>.json --alpha` (ou `--alpha prores` si la version de CapCut ne lit pas le codec QuickTime Animation).
2. Vérifie que `out/<slug>/capcut/` contient : `<slug>_final.mp4`, `<slug>_clean.mp4`, `<slug>_overlay_alpha.mov`, `captions.en.srt`, `stills/`, `timeline.csv`, `IMPORT_CAPCUT.md`.
3. Explique à l'utilisateur : CapCut n'a pas d'API de dépôt ; il faut glisser le dossier dans CapCut (bureau ou web) ou dans CapCut Cloud, puis suivre `IMPORT_CAPCUT.md`.
4. Rappelle de tester d'abord la transparence de `<slug>_overlay_alpha.mov` sur quelques secondes ; si le fond devient noir, utiliser `<slug>_final.mp4`.
