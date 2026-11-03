---
name: production-quotidienne
description: Orchestrer la production automatique du jour : jour 1 une vidéo longue (16:9), jour 2 un short lié à cette longue, avec veille, script, voix, rendu, contrôle qualité et emballage, dans les limites de quota et de temps. À utiliser pour la tâche planifiée quotidienne ou quand on demande « fais la vidéo du jour ».
---

# Production quotidienne (alternance longue / short lié)

## 0. Décider
`cd video-engine && node tools/daily-plan.mjs` → type du jour (longue ou short), vidéo concernée, étape, et alertes (short orphelin, liens incohérents). Un short sans longue liée ne se publie pas.

## 1. Journée « longue » (10 min, 16:9)
veille (`veille-virale` + `veille-sujets-finance`) → fiche d'impact (`economiste-impact-france`) → vérification (`verificateur-faits`) → script par chapitres (`script-long-educatif`) → voix (une requête par chapitre) → rendu **par blocs** → `controle-qualite-video` → emballage (`emballage-youtube`) → mise à jour de `serie/serie.json` (statut `rendu`).

## 2. Journée « short » (60 s, 9:16), toujours lié
Prendre le chapitre le plus fort de la longue de la veille, le réécrire en 60 s (accroche immédiate, 1 idée), renvoyer vers la longue en chute, rendre, contrôler, emballer. La voix du short suit celle de la longue.

## Limites à respecter (mesurées)
- **Voix Gemini gratuite : 10 requêtes par jour et par modèle.** Longue ≈ 9 requêtes (chapitres), short ≈ 5 à 10. Alternance longue/short = le quota tient ; ne jamais lancer deux longues le même jour avec le même modèle. Sur erreur 429 « par jour » : s'arrêter, noter l'heure de reprise, ne pas insister.
- **Rendu** : ≈ 1,3 image/s sur 4 cœurs ; 10 min = 18 000 images ≈ plusieurs heures. Rendre par blocs (`--frames`), assembler avec ffmpeg, supprimer les blocs ; ne pas dépasser le disque disponible (`df -h`).
- **Réseau** : sources officielles, banques d'images et plateformes ne sont accessibles que si leurs domaines sont autorisés dans l'environnement. Tester d'abord (`curl -s -o /dev/null -w "%{http_code}" <url>`) ; si bloqué, le dire, travailler avec ce qui est accessible, ne rien inventer.
- **Aucune publication automatique.** Le résultat est livré (fichiers, SEO, rapport) ; l'utilisateur publie.
- Clés API : variables d'environnement seulement, jamais dans un fichier ni un commit.

## Fin de journée
Commit des projets/sources (pas des médias lourds), rapport court : ce qui est fait, mesuré, vérifié, non vérifié, bloqué, prochaine étape (`daily-plan`).
