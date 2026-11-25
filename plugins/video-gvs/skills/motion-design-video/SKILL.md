---
name: "motion-design-video"
description: "Fabriquer en code une vidéo en motion design (16:9 ou 9:16) : personnage dessiné qui fait des exercices ou des gestes, textes et cartes animés, explications pas à pas, musique originale. Rendu image par image depuis une page HTML canvas. À utiliser pour les vidéos d'exercices, tutoriels et explications animées sans tournage."
---

# Vidéo en motion design codée

Modèle complet : `scripts/wellness-60.html` (« Gentle Wellness After 60 », 3 min 35, 8 exercices sur chaise). Rendu : `scripts/render.js` (Node + Playwright + ffmpeg). Musique : `scripts/music.py` (numpy).

## Principe
- Toute l'animation est une fonction `render(t)` qui dessine l'image au temps t (secondes) sur un canvas 1920×1080. Déterministe : pas de hasard non fixé, pas d'horloge.
- La page expose `window.DURATION`, `window.CHIMES` (débuts d'exercice) et `window.SFX` (moments sonores pour la skill sound-design-auto).
- Ouvrir la page dans un navigateur donne un aperçu ; `?t=130` saute à 130 s.

## Étapes
1. Écrire la timeline : segments (titre, pourquoi, précautions, un segment par exercice, plan, fin) avec leur durée. Pour un exercice : 2,6 s de carte d'intro (numéro, nom, catégorie) puis 18 s de démonstration.
2. Le personnage : squelette de 14 points (tête, cou, épaules, coudes, mains, hanches, genoux, pieds), poses-clés de face (`STAND`, `SEAT`) et de profil (`SEAT_S`, `LEAN_S`, `MID_S`, `STAND_S`). Chaque exercice = une fonction `pose(u)` qui mélange les poses avec un easing. Mouvements lents et réalistes pour un public senior.
3. Panneau d'explication : nom, catégorie, 3 ou 4 consignes qui apparaissent une à une (la consigne en cours en gras et surlignée, les précédentes cochées et estompées), nombre de répétitions, barre de progression. Points de la séance en haut à droite.
4. Vérifier avant le rendu complet : `node render.js page.html --stills 3,24,64,150 --dir stills`, assembler une planche avec ffmpeg (`tile`) et la regarder. Contrôler : texte qui dépasse, membres mal placés, chaise qui traverse le corps.
5. Rendu : `node render.js page.html --out video-muette.mp4` (environ 1,5 s de calcul par seconde de vidéo ; lancer en arrière-plan).
6. Musique : `python music.py --duration <durée> --chimes <débuts> --out musique.wav` (nappes d'accords, petite mélodie, carillon au début de chaque exercice ; synthétisée, donc sans droits).
7. Son : passer par la skill sound-design-auto, ou mixer la musique seule avec `loudnorm=I=-14:TP=-1.5`.

## Style
- Palette douce (crème, vert d'eau, corail), police Inter, fonds en dégradé avec formes floues qui dérivent lentement.
- Apparitions avec `outBack` (léger rebond), sorties en fondu de 0,5 s ; jamais plus de 3 éléments qui bougent en même temps.
- Textes à l'écran : courts, en phrases simples, auto-humaniser appliqué ; textes grands (32 px minimum en 1080p).
- Santé : carte « Before you start » (chaise stable, sans douleur, avis du médecin) et rappel « stop if it hurts » dans le plan.

## Voix off
Ajouter ensuite une voix (skill voix-chirp-antigravity ou Gemini) : écrire un texte par segment, régler la durée des segments sur la durée de la voix, puis mixer.
