---
description: "Analyser une vidéo étape par étape (hook, rythme, texte, son, appel à l'action, score /100)"
---

Travaille dans le dossier `autovid-shorts/` : toutes les commandes et chemins ci-dessous s'entendent depuis ce dossier.

1. Copie la vidéo de l'utilisateur dans `entrees/analyse/` si elle n'est pas déjà dans le projet.
2. Lance `python outils/analyser-video.py <video> --transcrire` (plusieurs vidéos possibles → `analyses/comparatif.md`).
3. Lis `analyses/<nom>/rapport.md` puis les images `hook.jpg`, `texte-*.jpg`, `planche.jpg`, `fin.jpg`.
4. Complète l'étape 9 du rapport en suivant `.claude/agents/analyste-video.md`.
5. Donne à l'utilisateur le score, les 3 raisons principales et la recette à reprendre.
