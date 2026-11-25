---
name: "animation-synchro-voix"
description: "Coder l'animation de personnages synchronisée sur la voix (bouche, regard, clignements, gestes, respiration, caméra) pour les films en pâte à modeler, avec un rendu vivant et touchant."
---

# Animation synchronisée sur la voix

Complète la skill film-pate-a-modeler (moteur rig-lib.js). Objectif : un personnage qui respire, regarde, parle et ressent, calé à l'image près sur l'audio.

## 1. Analyse audio avant l'animation
Pour chaque réplique (wav) calculer en Python (numpy) une piste par image (24 i/s) :
- env[f] : volume RMS sur 1/24 s, lissé (moyenne glissante 2 images), normalisé 0-1 → ouverture de bouche.
- accents : pics locaux d'env au-dessus de 0,7 → instants des syllabes fortes (pour les hochements et gestes).
- silences : env < 0,08 pendant plus de 0,15 s → bouche fermée, moments de respiration.
- formes de bouche simples déduites du spectre : énergie basse dominante → « O » arrondi ; énergie haute → « I/E » étiré ; sinon « A ».
Écrire tout dans timeline.json : { segments:[{debut, fin, perso, plan, emotion}], pistes:{perso:{env:[], forme:[], accents:[]}} } et le charger dans la page.

## 2. Visage
- Bouche : hauteur = 2 + 22×env (px à l'échelle tête), largeur selon la forme ; fermer 1 image avant chaque silence.
- Clignements : toutes les 2,5 à 5 s (aléatoire déterministe), 3 images ; un clignement juste après une phrase forte ; jamais pendant un regard intense.
- Regard : la pupille vise l'autre personnage ; détourner le regard (vers le bas, 0,6 s) avant un aveu ou quand le personnage a honte ; revenir sur « je » ou « toi ».
- Sourcils : intérieur relevé = tristesse, abaissé = colère/effort, les deux relevés = surprise ; transition en 6 images.
- Larmes : une goutte qui se forme (0,5 s), puis coule le long de la joue (1,5 s) ; brillance des yeux (petit reflet qui grossit) 1 s avant.

## 3. Corps
- Respiration permanente : torse +-1,5 ° et épaules +-3 px sur un cycle de 3,5 s ; plus rapide (1,8 s) en stress ; grande inspiration visible avant une phrase importante.
- Hochements de tête sur les accents (3 à 5 °, 5 images), jamais sur tous.
- Gestes : commencer 0,2 s AVANT le mot qu'ils accompagnent (anticipation), tenir, puis relâcher avec un léger dépassement (follow-through).
- Principes d'animation : anticipation, ralentis en début et fin (easing), chevauchement (la tête suit le buste avec 2-3 images de retard), poids (les épaules tombent dans la tristesse).
- Contact : pour une main sur l'épaule ou une étreinte, placer la main par cinématique inverse du bras (comme legIK) vers un point de l'autre personnage, recalculé à chaque image.
- Personnage qui écoute : jamais immobile (respiration, micro-mouvements de tête, clignements, réaction 0,3 s après le mot qui le touche).

## 4. Caméra et lumière
- Chaque plan du découpage = { cible, cadrage (large/taille/gros plan/très gros plan), zoom de départ et de fin }. Gros plan visage : zéro tremblement, poussée lente 3-6 %.
- Profondeur : flouter le décor (feGaussianBlur 6-10) en gros plan ; vignette sombre.
- Lumière : nuit froide (bleu, contraste fort) pour le présent ; contre-jour doré + halo pour le futur ; mélange progressif quand l'espoir revient.

## 5. Contrôle
- Générer une planche (1 image par plan) + 3 extraits courts de 2 s en vidéo autour des répliques fortes ; vérifier que la bouche ne bouge que pendant la voix du personnage qui parle, et que le décalage est inférieur à 2 images.
- Remettre toute amélioration du moteur dans moteur-animation (sorties) pour ne pas la perdre.