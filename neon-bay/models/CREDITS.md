# Modèles 3D
- `robot.glb` : RobotExpressive, par Tomás Laulhé (Quaternius), modifié par Don McCurdy. Licence CC0 1.0 (domaine public).
  Source : dépôt three.js, examples/models/gltf/RobotExpressive.

## Ajouter tes propres personnages
Tout fichier `.glb` animé (exporté de Blender, ou packs CC0 Quaternius / Kenney / KayKit) peut être déclaré dans `js/data.js` (`MODELS`). Le jeu cherche tout seul les animations dont le nom contient idle, walk, run, punch et death.

## Modèles originaux générés (Néon Bay)
Œuvres originales du projet, créées entièrement par code (scripts Blender/bpy dans `tools/blender/`) :
aucune géométrie, texture ou animation reprise d'un autre jeu ou d'un pack. Régénérables à l'identique
(`python3 tools/blender/gen_*.py`), mêmes droits que le reste du jeu.

- `car_sedan.glb`, `car_sports.glb`, `car_suv.glb`, `car_van.glb` : voitures (`gen_cars.py`).
- `human_m.glb`, `human_f.glb` : humains skinnés (version 2 : visage, mains avec pouce, vêtements en volume)
  avec animations Idle, Walk, Run, Punch, Death, Aim, AimRifle, Crouch (`gen_human.py`). Personnages inventés,
  ne représentant aucune personne réelle.
- `w_pistol.glb`, `w_uzi.glb`, `w_shotgun.glb`, `w_rifle.glb`, `w_sniper.glb`, `w_rocket.glb`, `w_minigun.glb`,
  `w_lmg.glb`, `w_gl.glb`, `w_rail.glb` : armes (`gen_weapons.py`). Designs génériques inventés : aucune
  reproduction d'une arme réelle, aucune marque.
- `palm.glb`, `lamp.glb`, `hydrant.glb`, `bench.glb`, `traffic_light.glb` : mobilier urbain (`gen_props.py`).
- Chaque `<nom>.glb.js` est la copie base64 du `.glb` correspondant (secours hors serveur).
- `previews/*.png` : rendus d'aperçu (`render_previews.py`).
