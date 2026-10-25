---
name: yt-retention
description: Analyse la rétention d'une vidéo (courbe YouTube Studio ou transcription) et indique où les spectateurs décrochent et quoi réécrire. Utiliser pour « rétention », « les gens partent », « audience retention », « durée de visionnage ».
---

# /yt-retention — où les gens partent

## Entrées
- Export CSV de la courbe de rétention (YouTube Studio → Analytics → Engagement), **et** la transcription horodatée ou le script.
- Sans courbe : fais une analyse prédictive sur le script seul, et dis clairement qu'elle est prédictive.

## Analyse
1. Repère les **chutes** : pente > 2 points de rétention en 5 s, et les **bosses** (revisionnages).
2. Aligne chaque chute avec la phrase prononcée à ce moment.
3. Diagnostique avec ces causes, dans cet ordre : intro trop longue (> 8 s avant la promesse) · promesse déjà tenue · bloc sans visuel > 6 s · répétition · digression · CTA trop tôt.
4. Compare la rétention à 30 s avec la moyenne de la chaîne si fournie.

## Sortie
Tableau `horodatage · chute · phrase · cause · réécriture proposée`, puis les 3 règles à ajouter dans `profil/voice.md` pour ne plus refaire l'erreur.
