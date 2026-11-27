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

## Effets de cinéma (panneau Film)
- **Coupe franche** : sur une clé, « Après cette clé : Coupe franche » pour passer au plan suivant sans mouvement (bande-annonce, clip).
- **Viser par plan** : chaque clé de caméra peut suivre un objet différent.
- **Tremblement** : par clé de caméra (poursuites, décollage, explosions).
- **Ralenti « bullet time »** : l'action ralentit, la caméra continue ; à terminer sur une coupe.
- **Titres** dans l'image (donc dans la vidéo exportée) : titre centré, carton noir, bandeau bas, logo néon sur deux lignes (MOT1|MOT2).
- **Flash blanc**, **fondus** d'ouverture et de fin, **étalonnage** : bleu-orange, néon saturé, film noir, doré.
- Nouveaux éléments : mer à vagues, ambiance Lune (ciel noir, Terre dans le ciel).

## Cinémathèque (scènes prêtes)
Bande-annonce complète (46 s, 12 plans), Poursuite de nuit, Arrivée à Morro Azul, Face-à-face, Décollage de la fusée.

## Générateur 3D (texte ou photo)
- Décris un objet (« un phare breton », « une moto de course néon ») ou donne une photo : Claude conçoit le modèle pièce par pièce (formes, matières, lumières) et le studio le construit aussitôt, à la bonne taille en mètres.
- « Modifier par IA » : une phrase suffit (« ajoute des ailes », « rouge mat », « deux fois plus grand ») ; le reste du modèle ne bouge pas.
- « Exporter GLB » : un .zip avec le modèle .glb (s'ouvre dans Blender, Unity, Unreal, Godot, three.js) et sa description .json.
- Trois modèles d'exemple marchent sans connexion : moto néon, hélicoptère, food truck.
- La création consomme l'usage Claude de la personne qui l'utilise ; Claude demande l'autorisation au premier usage.

## Rendu cloud (qualité maximale, MP4 H.264)
```
node tools/build-web.js
node tools/studio/render.js --template chase --res 1080      # scènes prêtes : chase, arrival, duel
node tools/studio/render.js mon-projet.json --res 1080        # un projet exporté depuis le studio
node tools/studio/render.js --template trailer --music usa --hot 7-14,21-36   # avec la musique du jeu
```
La vidéo sort dans `marketing/studio/`. Le rendu se fait image par image : aucune saccade, même sur un téléphone lent.
