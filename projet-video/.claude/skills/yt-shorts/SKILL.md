---
name: yt-shorts
description: "Extrait 2 à 5 Shorts verticaux d'une vidéo longue (ou écrit un Short de zéro) avec hook réécrit, sous-titres et video.json prêt pour le rendu Remotion. Utiliser pour « Shorts », « Reels », « TikTok », « clip vertical », « découpe en Shorts »."
---

# /yt-shorts

## Repérer les passages
Dans la transcription de la vidéo longue, cherche des passages de 25 à 50 s qui :
- tiennent seuls (pas de « comme je disais »),
- contiennent un chiffre, une démo ou un retournement,
- se terminent sur une phrase forte (le Short boucle mieux).

## Pour chaque Short
1. Réécris les 3 premières secondes avec une formule de `yt-script/formules.md` (le hook d'une vidéo longue n'est presque jamais le bon hook de Short).
2. Format du gabarit : 1080×1920, visuels en haut, facecam en bas, sous-titres sur la ligne de coupe, 1 mot rouge par segment.
3. Termine par un CTA « commente <MOT> » si l'utilisateur a une ressource à envoyer, sinon « la vidéo complète est sur la chaîne ».
4. Génère `remotion/data/short-<n>.json` (même format que `/yt-edit`).

Sortie : tableau `n · début–fin dans la longue · hook réécrit · mot du CTA` et les fichiers JSON.
