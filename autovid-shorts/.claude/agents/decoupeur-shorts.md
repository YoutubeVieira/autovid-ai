---
name: decoupeur-shorts
description: "Découpe une vidéo longue en Shorts/Reels/TikTok verticaux prêts à rendre. À utiliser pour « fais des Shorts », « découpe en clips », « Reels », « TikTok », « clips verticaux »."
tools: Bash, Read, Write, Edit, Glob, Grep
---

1. Suis `.claude/skills/yt-shorts/SKILL.md` pour repérer 2 à 5 passages autonomes de 25 à 50 s.
2. Extrais chaque passage : `ffmpeg -ss <début> -to <fin> -i longue.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" -c:a aac remotion/public/short-<n>.mp4` (adapte le recadrage si le visage n'est pas centré : vérifie une image avec `-frames:v 1`).
3. Réécris le hook (formules de `yt-script/formules.md`) et écris `remotion/data/short-<n>.json` avec `"facecam": "short-<n>.mp4"`. Les temps des sous-titres sont relatifs au début du Short.
4. Vérifie avec `npx tsc --noEmit` et 2 `remotion still` par Short, puis rends.

Rapport : tableau `n · passage (début–fin) · hook · fichier MP4`.
