---
name: yt-chapters
description: Génère les chapitres YouTube (horodatages) d'une vidéo longue à partir de sa transcription. Utiliser pour « chapitres », « timestamps », « horodatages », « chapters ».
---

# /yt-chapters

Règles YouTube : le premier chapitre commence à `00:00`, au moins 3 chapitres, chacun ≥ 10 s.

1. Découpe la transcription par changement de sujet (pas par durée fixe).
2. Titre de chapitre : 2 à 6 mots, contient le mot-clé du passage, pas de numérotation.
3. Le chapitre qui contient le « payoff » porte un titre qui donne envie (« Le résultat final »), pas « Conclusion ».

Sortie : bloc prêt à coller dans la description.
```
00:00 <titre>
01:12 <titre>
```
