# Réalisation TikTok : le « moteur producteur-scénariste »
Outil : `realisation/realisation.py` (scénario annoté + `voice.json` -> `decoupage.json/.md`). Agent : `scenariste-producteur`.

## 1. Structure d'un épisode (25-30 s)
| Rôle | Temps | Ce qui se passe à l'écran |
|---|---|---|
| **Hook** | 0-3 s | texte écrit + mouvement + voix dès 0,15 s ; plan LARGE spectaculaire (le décor, l'enjeu), ouverture « Dans cette ville… » |
| Contexte | 3-8 s | plan moyen, on montre qui/quoi |
| Montée | 8-20 s | changement visuel **toutes les ≤ 2,5 s**, on serre (large → moyen → gros plan) |
| Climax | ~70 % | silence 0,3 s + riser, puis plan serré / contre-plongée, boom |
| Payoff + CTA | fin | plan chaleureux, appel (« commente ton prénom ») ; boucle/teaser de l'épisode suivant |
Option > 60 s : ajouter un mini-accroche de relance vers 15 s et 30 s.

## 2. Émotion -> plan, caméra, zoom, visage, son
| Émotion | Plan | Caméra / zoom | Visage | Son / effet |
|---|---|---|---|---|
| Peur | gros plan | push-in rapide 1.0→1.25 + tremblement | scared | gasp |
| Surprise | gros plan | punch-in 1.0→1.18 + flash blanc | surprise | oh_surprise |
| Joie | moyen | orbite légère | happy/laugh | giggle |
| Tristesse | large | pull-out lent 1.12→1.0, désaturé | sad/cry | musique calme |
| Colère | gros plan en contre-plongée | tremblement | angry | stomp |
| Suspense | moyen | push-in lent 1.0→1.1 | smile | riser |
| Fierté / victoire | contre-plongée | tilt up | happy | level_up + étincelles |
| Curiosité | insert (détail) | push-in lent | surprise | tick |
| Amour | gros plan | maintien doux | love | sparkle |

## 3. Quand les personnages parlent (dialogues)
- Annoter la réplique avec `"qui": "Mamie"` : le plan est sur celui qui parle (🗣 = bouche animée), voix du casting (`packs/voices/cast.json`).
- **Plan de réaction** (0,7 s) du personnage qui écoute à la fin de la réplique (`"ecoute": "Robin"`).
- Un seul orateur à l'écran à la fois ; jamais plus de 3 répliques sans changer de plan.
- Sous-titres : 1 à 3 mots, mot fort en couleur ; **punch-in 1.2 pendant 0,18 s sur le mot fort**.

## 4. Règles de montage (le moteur vérifie)
1. Jamais deux fois le même plan d'affilée. 2. Aucun plan > 3,3 s. 3. Hook avant 0,5 s. 4. Taille de plan en progression vers le pic émotionnel. 5. Sons : un seul bruitage important par temps fort, musique en ducking sous la voix, -14 LUFS.
6. Mouvements : whip-pan / flash pour les transitions de lieu, push-in pour la tension, pull-out pour le soulagement ou la tristesse.

## 5. Sources et prudence
Ces règles viennent de la grammaire du cinéma (gros plan = intimité/émotion, plan large = échelle, réaction, progression de taille) et de conseils de créateurs : [Adobe, types de plans](https://www.adobe.com/creativecloud/video/discover/types-of-shots-in-films.html), [Basic Cinematography for Animation](https://courses.cs.washington.edu/courses/cse456/09su/resources/Basic%20Cinematography%20for%20Animation.pdf), [Opus, TikTok first 3 seconds](https://www.opus.pro/blog/viral-tiktoks-first-3-seconds-2026), [Nemo, retention](https://www.nemovideo.com/blog/how-to-edit-tiktok-videos). **Les chiffres (hook en 3 s, un changement visuel toutes les 2-3 s) sont des règles empiriques de blogs, non confirmées par TikTok** : à tester avec la courbe de rétention de TikTok Analytics et à ajuster.

## 6. Utilisation
1. Écrire le script, générer la voix (`tts.py`) -> `voice.json`.
2. Annoter `beats.json` (rôle, émotion, qui parle, mot fort), lancer `realisation.py`.
3. Lire `decoupage.md` (tableau plan par plan) ; corriger si l'audit signale un problème.
4. Rendu Blender : `episode_monde.py -- ... --decoupage decoupage.json` place caméras, zoom d'objectif, expressions, sons et effets (événements punch/flash/shake lus par le preset `monde_tiktok`). `python3 monde/monde.py beats --episode N` annote automatiquement le script d'un épisode.
Exemple : `monde/episodes/ep00/decoupage.md`.
