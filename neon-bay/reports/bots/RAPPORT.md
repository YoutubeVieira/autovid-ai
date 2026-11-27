# Rapport des 20 testeurs automatiques

Date : 2026-11-21 20:11 UTC · niveaux 1 à 30 · 2 essais maximum par niveau.

> Les testeurs jouent avec les mêmes règles qu'un joueur (vitesse de marche et de conduite, tir, police, chronos), sans téléportation, en simulation accélérée. Ils conduisent et visent moins bien qu'un bon joueur humain : leurs temps sont des **ordres de grandeur**, et leurs échecs montrent **où** le jeu est dur, pas exactement **combien**.

## Résultats par testeur

| # | Testeur | Fonction | Difficulté | Niveaux réussis | Temps de jeu | Essais | Cause d'échec n° 1 |
|---|---|---|---|---|---|---|---|
| 1 | Débutant prudent | Mesure si un nouveau joueur finit le jeu en Facile | Facile | 0/30 | 145 min | 60 | Tu as été mis K.O. (elim) ×12 |
| 2 | Joueur moyen | Référence : temps typique pour finir les 30 niveaux en Normal | Normal | 0/30 | 121 min | 60 | Tu as été mis K.O. (elim) ×18 |
| 3 | Expert | Temps plancher d’un très bon joueur | Normal | 0/30 | 125 min | 60 | Tu as été mis K.O. (elim) ×19 |
| 4 | Speedrunner | Toujours en voiture, nitro, aucun détour : chemin le plus rapide | Normal | 0/30 | 95 min | 60 | Tu as été mis K.O. (elim) ×18 |
| 5 | Légende | Vérifie que la difficulté Légende reste faisable | Légende | 0/30 | 100 min | 60 | Tu as été mis K.O. (elim) ×25 |
| 6 | Difficile | Équilibrage du mode Difficile | Difficile | 0/30 | 99 min | 60 | Tu as été mis K.O. (elim) ×21 |
| 7 | Piéton pur | Ne prend une voiture que si l’étape l’exige : chronos des étapes à pied | Normal | 0/30 | 99 min | 60 | Tu as été mis K.O. (elim) ×19 |
| 8 | Gros acheteur | Dépense tout : armes, armures, soins. L’économie suit-elle ? | Normal | 0/30 | 117 min | 60 | Tu as été mis K.O. (elim) ×20 |
| 9 | Radin | N’achète rien : le jeu se finit-il sans boutique ? | Normal | 1/30 | 91 min | 59 | Tu as été mis K.O. (elim) ×22 |
| 10 | Entraîné | Achète l’entraînement en priorité : impact de la salle de sport | Normal | 0/30 | 109 min | 60 | Tu as été mis K.O. (elim) ×22 |
| 11 | Tunnelier | Sème la police par les tunnels plutôt qu’en voiture | Normal | 1/30 | 148 min | 60 | Tu as été mis K.O. (elim) ×23 |
| 12 | Sans soins | N’utilise jamais de trousse : la régénération suffit-elle ? | Normal | 0/30 | 120 min | 60 | Tu as été mis K.O. (elim) ×20 |
| 13 | Sans armure | N’achète jamais d’armure | Normal | 0/30 | 106 min | 60 | Tu as été mis K.O. (elim) ×26 |
| 14 | Mauvais tireur | Vise mal : le jeu reste-t-il jouable pour un joueur maladroit ? | Normal | 0/30 | 109 min | 60 | Tu as été mis K.O. (elim) ×22 |
| 15 | Bagarreur | Poings uniquement : limite du corps à corps | Normal | 0/30 | 132 min | 60 | Tu as été mis K.O. (elim) ×17 |
| 16 | Arme lourde | Achète la meilleure arme dès qu’il peut | Normal | 0/30 | 102 min | 60 | Tu as été mis K.O. (elim) ×18 |
| 17 | Chasseur de contrats | N’achète aucune arme : les armes gratuites par défis suffisent-elles ? | Normal | 0/30 | 114 min | 60 | Tu as été mis K.O. (elim) ×21 |
| 18 | Réflexes lents | Réagit 2,5 fois plus lentement (joueur sur petit téléphone) | Normal | 1/30 | 132 min | 59 | Tu as été mis K.O. (elim) ×17 |
| 19 | Sans reprise | Recommence toujours depuis l’étape 1 : utilité du point de reprise | Normal | 0/30 | 114 min | 60 | Tu as été mis K.O. (elim) ×17 |
| 20 | Explorateur | Fait des détours (30 % du temps hors GPS) : le chrono reste-t-il tenable ? | Normal | 0/30 | 113 min | 60 | Tu as été mis K.O. (elim) ×17 |

## Difficulté par niveau

| Niveau | Réussite (testeurs) | Temps médian d'une réussite | Étape la plus bloquante |
|---|---|---|---|
| 1 | 1/20 | 2 min | escape (11 échecs) |
| 2 | 0/20 | — | escort (22 échecs) |
| 3 | 2/20 | 7 min | collect (19 échecs) |
| 4 | 0/20 | — | race (24 échecs) |
| 5 | 0/20 | — | destroy (21 échecs) |
| 6 | 0/20 | — | jailbreak (39 échecs) |
| 7 | 0/20 | — | destroy (22 échecs) |
| 8 | 0/20 | — | escort (23 échecs) |
| 9 | 0/20 | — | bribe (10 échecs) |
| 10 | 0/20 | — | escort (14 échecs) |
| 11 | 0/20 | — | destroy (25 échecs) |
| 12 | 0/20 | — | elim (17 échecs) |
| 13 | 0/20 | — | jailbreak (40 échecs) |
| 14 | 0/20 | — | elim (23 échecs) |
| 15 | 0/20 | — | collect (22 échecs) |
| 16 | 0/20 | — | buy (36 échecs) |
| 17 | 0/20 | — | elim (37 échecs) |
| 18 | 0/20 | — | elim (34 échecs) |
| 19 | 0/20 | — | destroy (37 échecs) |
| 20 | 0/20 | — | elim (23 échecs) |
| 21 | 0/20 | — | elim (34 échecs) |
| 22 | 0/20 | — | survive (20 échecs) |
| 23 | 0/20 | — | elim (36 échecs) |
| 24 | 0/20 | — | collect (24 échecs) |
| 25 | 0/20 | — | escort (20 échecs) |
| 26 | 0/20 | — | elim (33 échecs) |
| 27 | 0/20 | — | elim (39 échecs) |
| 28 | 0/20 | — | race (40 échecs) |
| 29 | 0/20 | — | survive (39 échecs) |
| 30 | 0/20 | — | elim (40 échecs) |

## Pourquoi on perd

| Cause | Nombre |
|---|---|
| Tu as été mis K.O. | 854 |
| Temps écoulé | 182 |
| Arrêté par la police | 48 |
| bloqué | 44 |
| MC Ozone n’a pas survécu | 27 |
| Tyrell n’a pas survécu | 15 |
| Nino n’a pas survécu | 12 |
| il Consigliere n’a pas survécu | 10 |
| DJ Favelinha n’a pas survécu | 2 |
| Rosa n’a pas survécu | 1 |

## Étapes qui font perdre

| Type d'étape | Échecs |
|---|---|
| elim | 395 |
| escort | 125 |
| destroy | 116 |
| race | 94 |
| collect | 91 |
| jailbreak | 85 |
| survive | 70 |
| escape | 49 |
| buy | 47 |
| bribe | 38 |
| goto | 33 |
| deliver | 19 |

## Chronos : vitesse moyenne exigée sur la route

Voiture du joueur : 520 au maximum. Au-delà d'environ 280 de moyenne, un joueur sur téléphone a du mal.

| Type d'étape | Mesures | Vitesse exigée (médiane) | Pire cas |
|---|---|---|---|
| garage | 95 | 36 | 59 |
| deliver | 48 | 74 | 117 |
| race | 101 | 134 | 255 |

## Erreurs techniques

Aucune erreur du jeu pendant les parties.

## Ce que les testeurs nous apprennent (stratégies)

- Acheter de l’équipement : Gros acheteur 0 niveaux contre Radin 1.
- S’entraîner à la salle : Entraîné 0 niveaux contre Joueur moyen 0.
- Semer la police par les tunnels : Tunnelier 1 niveaux contre Joueur moyen 0.
- Rouler vite en voiture : Speedrunner 0 niveaux contre Joueur moyen 0.
- Rester à pied : Piéton pur 0 niveaux contre Joueur moyen 0.
- Se passer des trousses de soins : Sans soins 0 niveaux contre Joueur moyen 0.
- Jouer sans armure : Sans armure 0 niveaux contre Joueur moyen 0.
- Le point de reprise à l’étape 6 : Sans reprise 0 niveaux contre Joueur moyen 0.
- Armes gratuites par défis contre achat : Chasseur de contrats 0 niveaux contre Arme lourde 0.
- Viser mal contre viser bien : Mauvais tireur 0 niveaux contre Expert 0.
- Facile contre Normal : Débutant prudent 0 niveaux contre Joueur moyen 0.
- Légende contre Difficile : Légende 0 niveaux contre Difficile 0.
