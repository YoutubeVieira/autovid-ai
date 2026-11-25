---
description: "Créer un Short / Reel de A à Z : sujet, script, montage, sons, rendu"
---

1. Sujet et hook : suis `.claude/agents/scenariste.md` (script dans `scripts/<slug>.md`).
2. Montage : suis `.claude/agents/monteur-video.md` (prise brute dans `entrees/<slug>/` si l'utilisateur en a une) → `remotion/data/<slug>.json`.
3. Vérifie : `cd remotion && npx tsc --noEmit`, puis 4 images de contrôle avec `npx remotion still`.
4. Rends : `npx remotion render AutoVidShort out/<slug>.mp4 --props=./data/<slug>.json`.
5. Donne le chemin du MP4, sa durée, et propose `/superanalyse` sur le résultat.
