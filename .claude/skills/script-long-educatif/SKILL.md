---
name: script-long-educatif
description: Écrire une vidéo longue (8 à 12 min, 16:9) éducative au rythme « TikTok » : accroche qui fait réfléchir, chapitres, relances toutes les 30-45 s, exemples chiffrés, sources et mention finale. Produit le projet JSON du moteur video-engine découpé en chapitres. À utiliser pour la vidéo longue du jour.
---

# Script de vidéo longue éducative

Entrée : fiche `veille/fiches/<slug>.md` validée (registre de faits). Sortie : `projects/<slug>.json` (`"format": "16:9"`, scènes groupées par `"chapter"`).

## Structure (≈ 1 500 mots, ≈ 10 min, 9 chapitres, 1 requête de voix par chapitre)
1. **Accroche (0-30 s)** : une situation concrète qui fait réfléchir (« deux personnes empruntent la même somme… »), une question ouverte, la promesse de la vidéo, sans introduction ni « bonjour ».
2. **Chapitres 2 à 8** : un maillon de la chaîne cause → effet par chapitre, 60 à 80 s chacun. Chaque chapitre : question → explication → exemple chiffré ou schéma → mini-conclusion qui ouvre le suivant.
3. **Nuances (chapitre 8)** : ce qui est incertain, les cas où l'effet est faible ou absent, les limites de l'exemple.
4. **Que retenir (chapitre 9)** : 3 idées, gestes d'éducation financière génériques, avis « contenu éducatif, aucune obligation d'achat, pas un conseil en investissement », appel à s'abonner, renvoi vers le short lié et la vidéo suivante.

## Rythme « TikTok éducatif »
- Une idée par phrase (≤ 18 mots), tutoiement, vocabulaire du quotidien ; chaque terme technique est défini à sa première apparition.
- Un changement visuel toutes les 3 à 6 s : nouvelle scène, zoom, chiffre qui défile, flèche, encart, bandeau de chapitre. Jamais plus de 8 s sur le même plan.
- Boucles ouvertes : annoncer ce qu'on va voir plus tard (« on arrive au chiffre qui surprend le plus »), puis tenir la promesse.
- Sous-titres 3 mots, bruitages sur les ruptures, silence avant une révélation.
- Un exemple chiffré **calculé** (formule et hypothèses affichées) vaut mieux qu'un chiffre de marché non vérifié.

## Médias
- Images ou vidéos déposées par l'utilisateur dans `public/media/` (NASA, Google Earth, archives libres) : item `media` avec **mention de source obligatoire** ; vérifier la licence et les règles de mention avant de les utiliser.
- Sans média fourni, produire soi-même : carte, globe 3D (Natural Earth), schémas, compteurs. Ne jamais simuler une image NASA ou Google Earth.

## Contrôles avant voix et rendu
`npm test` (faits, médias, voix), `verificateur-faits` sur la fiche et le script, puis `controle-qualite-video` après rendu.
Lien avec le short : marquer dans le script le chapitre qui sera décliné en short (`"short": "S1"` sur la scène de départ).
