---
name: produire-video-finance
description: Chef d'orchestre de la chaîne « vidéo finance France » : veille → analyse de référence → fiche d'impact → vérification des faits → script/JSON → rendu → contrôle. À utiliser quand l'utilisateur dit « fais-moi une vidéo sur… », « trouve la prochaine vidéo », ou demande tout le pipeline.
---

# Produire une vidéo finance : le flux complet

Chaque étape a un **agent** et un **livrable**. On n'avance pas tant que la porte de contrôle n'est pas passée.

| # | Étape | Agent | Livrable | Porte de contrôle |
|---|---|---|---|---|
| 1 | Trouver le sujet | `veilleur-sujets` | `veille/AAAA-MM-JJ-idees.md` | l'utilisateur choisit **un** sujet |
| 2 | Analyser la référence (si « refaire ») | `analyste-video-reference` | `veille/analyses/<nom>.md` | écarts moteur listés |
| 3 | Fiche d'impact France | `economiste-impact-france` | `veille/fiches/<slug>.md` | chaque chiffre a source + date |
| 4 | Vérifier les faits | `verificateur-faits` | rapport OK / à corriger | aucun « non confirmé » restant |
| 5 | Écrire script + JSON | `scenariste-carte` | `projects/<slug>.json` | `npm test` passe |
| 6 | Voix + rendu + image de contrôle | (soi-même) | `out/<slug>.mp4` | images regardées, son écouté/mesuré |
| 7 | Relecture finale | `verificateur-faits` | rapport | chiffres à l'écran = faits |

## Règles du flux
- Lancer les agents **en parallèle** quand ils sont indépendants (ex. plusieurs idées à documenter) ; **en série** quand l'un nourrit l'autre.
- L'utilisateur valide aux étapes 1 et 4. Ne pas publier, ne rien envoyer à l'extérieur.
- Si une donnée manque ou se contredit : la vidéo l'annonce (« estimation ») ou la scène est retirée. On n'arrondit pas pour faire joli.
- Si la scène demande un fond hors Europe : étendre le fond de carte **avant** de scénariser.
- Rendre compte honnêtement : ce qui est vérifié (sources ouvertes), ce qui ne l'est pas, ce qui a été regardé/écouté ou seulement généré.
