# Gym Douce Senior — système graphique pastel

## Direction artistique
Identité douce, naturelle, lumineuse et apaisante pour des séances YouTube destinées aux 60–85 ans. Coach 3D réaliste en plein écran, textes discrets en surimpression, sans cadres permanents.

## Charte graphique
- Vert sauge `#8FB996` : éléments actifs et progression.
- Beige clair `#F6F4EC` : décor, ambiance et surfaces douces.
- Vert olive `#5B725E` : titres et textes sur fond clair.
- Jaune doux `#F6C667` : conseils importants, avec parcimonie.
- Gris chaud `#A7B0A6` : informations secondaires.
- Blanc `#FFFFFF` : texte sur zone sombre uniquement.
- Titres : Montserrat SemiBold.
- Consignes : Inter Medium.
- Chronomètre : Roboto Mono Medium.
- Vidéo : 1920×1080, 16:9, 30 fps.

## Règles d’écran
1. Le coach reste en plein écran et visible en pied quand le mouvement l’exige.
2. Pas de panneaux ni de cadres permanents.
3. Nom de la séance en haut à gauche, discret.
4. Numéro de l’exercice en haut à droite, petit.
5. Nom de l’exercice, chronomètre et consigne apparaissent à droite uniquement quand il y a de l’espace visuel.
6. Utiliser une ombre très légère ou un halo doux derrière le texte si le décor est trop chargé, plutôt qu’un rectangle.
7. Une seule consigne courte à l’écran à la fois.
8. Éviter de recouvrir le visage, les mains, les pieds ou les articulations utiles.

## Animations
- Introduction : fondu doux de 0,5 s, titre visible 1,5 à 2 s.
- Nom de l’exercice : fondu de 0,35 s, sans déplacement brusque.
- Chronomètre : chiffres stables, sans rebond, décompte en temps réel.
- Barre de progression : fine, vert sauge, discrète.
- Flèche de mouvement : seulement si utile, visible environ 1 s.
- Transition repos : fondu de 0,4 s ; texte « Récupération » pendant 2–3 s.
- Fin de séance : « Bravo, vous avez pris soin de vous aujourd’hui ! » puis invitation discrète à s’abonner.
- Pas de flash, zoom agressif, clignotement ni effets sonores à chaque seconde.

## Introduction de 7 secondes
- 0–1,5 s : le coach sourit et salue ; texte discret « Gym Douce Senior ».
- 1,5–4,5 s : promesse, par exemple « 10 minutes pour travailler votre équilibre ».
- 4,5–7 s : le coach se met en position ; voix off « Prenez une chaise stable si nécessaire. Nous commençons ensemble. »

## Chronomètre et consignes
- Effort indicatif : 30–45 s selon l’exercice et le niveau.
- Repos indicatif : 15–20 s ou davantage selon les besoins.
- Format du compteur : `00:35`, avec Roboto Mono Medium.
- La progression doit correspondre à la durée réelle du segment.
- Pour un exercice en répétitions, afficher par exemple `08 / 12`.
- Ne pas afficher plusieurs compteurs concurrents.

## Structure type
### 10 minutes
Introduction 7 s ; échauffement environ 2 min ; bloc principal avec repos intégrés environ 6 min ; retour au calme et conclusion environ 1 min 45 s.
### 20 minutes
Introduction courte ; échauffement 3 min ; bloc principal 14–15 min ; retour au calme et conclusion sur le temps restant.
### 30 minutes
Introduction courte ; échauffement 4–5 min ; bloc principal 21–22 min ; retour au calme 3 min ; conclusion courte.
Ajuster les durées pour obtenir la durée totale exacte de la vidéo.

## Workflow Python + FFmpeg
1. Écrire les exercices, textes et durées dans `config.json`.
2. Exporter le coach animé depuis Blender, avec décor final ou fond transparent.
3. Générer les textes et éléments graphiques en PNG/SVG transparents.
4. Générer la voix off et les sous-titres SRT.
5. Assembler vidéo, voix, musique, titres et chronomètre avec FFmpeg.
6. Contrôler le timing, la lisibilité sur téléphone et télévision, et la visibilité du mouvement.
7. Exporter en H.264, 1080p, 30 fps, audio AAC 48 kHz.

## Exemple FFmpeg : ajouter un overlay
Suppose `overlay_intro.png` est une image 1920×1080 transparente :
```bash
ffmpeg -i coach.mp4 -i overlay_intro.png \
-filter_complex "[0:v][1:v]overlay=0:0:format=auto:enable='between(t,0,7)'" \
-c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium \
-c:a aac -b:a 192k -movflags +faststart sortie.mp4
```
Le chronomètre dynamique doit être calculé à partir des heures de début et de fin de chaque exercice dans le script de montage, pas par un minuteur indépendant.

## Sécurité et qualité
Proposer un appui sur une chaise stable ou une variante assise quand c’est pertinent. Rappeler de s’arrêter en cas de douleur, vertige ou essoufflement inhabituel. Garder la musique sous la voix et les consignes visibles assez longtemps pour être lues.
