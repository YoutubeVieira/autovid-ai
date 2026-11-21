# Néon Studio : créer des cinématiques 3D

Éditeur 3D dans le navigateur (téléphone ou PC), avec les modèles Blender de Néon Bay.

## Ce qu'on peut faire
- **Poser** des personnages animés (homme, femme, robot), des voitures (berline, sportive, SUV, fourgon, police), une rue néon complète, du mobilier, des formes, des enseignes et des lumières.
- **Animer** avec des images clés : place l'objet, avance la timeline, déplace-le à nouveau ; avec « Clé auto », chaque déplacement crée une clé. Les roues tournent toutes seules, les personnages marchent, courent, frappent ou tombent.
- **Filmer** avec une vraie caméra : focales de 24 à 135 mm, « Viser » un objet pour qu'elle le suive, « Caméra ici » pour copier le point de vue de l'éditeur.
- **Ambiances** : nuit néon, coucher de soleil, plein jour, orage ; halo néon, pluie, sol mouillé avec reflets ; vignette et grain de film.
- **Formats** : 16:9 (YouTube), 9:16 (TikTok), 2.39 (cinéma), en 720p ou 1080p.
- **Exporter** : image PNG, vidéo (enregistrée en temps réel par le navigateur), projet .json à recharger plus tard.

Raccourcis : Espace lecture · W/E/R déplacer, tourner, échelle · C vue caméra · K poser une clé · Suppr supprimer.

## Rendu cloud (qualité maximale, MP4 H.264)
```
node tools/build-web.js
node tools/studio/render.js --template chase --res 1080      # scènes prêtes : chase, arrival, duel
node tools/studio/render.js mon-projet.json --res 1080        # un projet exporté depuis le studio
```
La vidéo sort dans `marketing/studio/`. Le rendu se fait image par image : aucune saccade, même sur un téléphone lent.
