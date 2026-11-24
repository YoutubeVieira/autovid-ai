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
- `human_m.glb`, `human_f.glb`, `human_m2.glb` (trapu, sweat à capuche, casquette), `human_f2.glb` (jupe,
  queue de cheval) : humains skinnés (version 3 : doigts animés, textures procédurales cuites dans Blender —
  peau, maille, sergé, semelles — et normal maps tissu, mèches de cheveux en géométrie) avec animations Idle,
  Walk, Run, Punch, Death, Aim, AimRifle, Crouch (`gen_human.py`, `nb_textures.py`). Personnages inventés,
  ne représentant aucune personne réelle ; aucune photo ni texture externe.
- `w_pistol.glb`, `w_uzi.glb`, `w_shotgun.glb`, `w_rifle.glb`, `w_sniper.glb`, `w_rocket.glb`, `w_minigun.glb`,
  `w_lmg.glb`, `w_gl.glb`, `w_rail.glb` : armes, version 3 « vitrine » (`gen_weapons.py`) : formes
  biseautées, découpes booléennes (stries, fenêtres d'éjection, garde-mains ajourés, freins de bouche),
  rails à crans, organes de visée, vis, anneaux ; matériaux PBR (acier bruni avec usure claire des arêtes,
  polymère texturé, caoutchouc quadrillé, verre teinté émissif) et textures procédurales cuites dans
  Blender (`nb_textures.weapon_textures`, 256 px, normal maps). Designs génériques inventés : aucune
  reproduction d'une arme réelle, aucune marque ni marquage, aucune texture externe.
- `palm.glb`, `lamp.glb`, `hydrant.glb`, `bench.glb`, `traffic_light.glb` : mobilier urbain (`gen_props.py`).
- Chaque `<nom>.glb.js` est la copie base64 du `.glb` correspondant (secours hors serveur).
- `previews/*.png` : rendus d'aperçu (`render_previews.py`) ; planche des armes dans
  `tools/blender/previews/weapons_sheet.png` (`weapon_sheet.py`).
