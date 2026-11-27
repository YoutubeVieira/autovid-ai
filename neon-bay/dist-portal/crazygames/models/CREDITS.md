# Modèles 3D
- `robot.glb` : RobotExpressive, par Tomás Laulhé (Quaternius), modifié par Don McCurdy. Licence CC0 1.0 (domaine public).
  Source : dépôt three.js, examples/models/gltf/RobotExpressive.

## Ajouter tes propres personnages
Tout fichier `.glb` animé (exporté de Blender, ou packs CC0 Quaternius / Kenney / KayKit) peut être déclaré dans `js/data.js` (`MODELS`). Le jeu cherche tout seul les animations dont le nom contient idle, walk, run, punch et death.

## Modèles originaux générés (Néon Bay)
Œuvres originales du projet, créées entièrement par code (scripts Blender/bpy dans `tools/blender/`) :
aucune géométrie, texture ou animation reprise d'un autre jeu ou d'un pack. Régénérables à l'identique
(`python3 tools/blender/gen_*.py`), mêmes droits que le reste du jeu.

- `car_sedan.glb`, `car_sports.glb`, `car_suv.glb`, `car_van.glb`, `car_police.glb` : voitures version 3
  (`gen_cars.py`, kit `nb_vehicle.py`) : carrosserie lissée à lignes de caisse et passages de roue évasés,
  optiques en verre émissif, calandre ajourée, habitacle visible, jantes détaillées (disques, étriers,
  écrous), pneus à sculptures en normal map, plaques sans texte lisible ; voiture de police fictive
  (livrée bicolore, rampe de gyrophares, pare-buffle, emblème générique). Designs inventés : aucune
  marque, aucun logo, aucune calandre de constructeur réel.
- `army_jeep.glb`, `army_truck.glb`, `army_apc.glb` : véhicules militaires génériques (`gen_army.py`) :
  4x4 ouvert à arceaux, camion bâché 6 roues, blindé 8 roues à tourelle. Numéros au pochoir inventés,
  aucun insigne réel. Textures (pneus, plastique, toile, optiques, plaques) générées par numpy dans
  `nb_vehicle.py`, aucune source externe.
- Planches d'aperçu des véhicules : `tools/blender/previews/<nom>_sheet.png` et `vehicles_sheet.png`
  (`vehicle_sheet.py`).
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
- `lm_statue.glb` (« Statue de la Lumière » : femme drapée à la torche, couronne à 5 rayons, tablette « NB »,
  piédestal sur fort en étoile à 7 branches, îlot) et `lm_palace.glb` (« Palais présidentiel » néoclassique,
  portique ionique, drapeau fictif) : monuments inventés de Néon Bay, **inspirés** des grands symboles
  américains sans en copier aucun ni porter de nom réel (`gen_landmarks.py`).
- `prop_basket_hoop`, `prop_basket_court`, `prop_soccer_goal`, `prop_soccer_field`, `prop_boxing_ring`,
  `prop_ball_basket`, `prop_ball_soccer`, `prop_stadium_stand` (`.glb`) : équipements sportifs génériques,
  sans marque ni logo (`gen_landmarks.py`). Textures procédurales cuites dans Blender (marbre, pierre,
  patine, gazon, béton, toile, parquet + lignes du terrain dessinées par le script).
- `human_f3.glb` (sauveteuse : maillot une pièce sportif, short de bain, queue de cheval, lunettes de soleil
  sur la tête, sifflet), `human_m3.glb` (sauveteur : débardeur, short de bain, bob, tongs), `human_f4.glb` et
  `human_m4.glb` (danseurs de baile funk : crop top / maillot de foot à numéro, jogging à bandes, baskets
  montantes, chaînes, chignon / casquette), `human_m5.glb` (prisonnier : combinaison orange, tatouages
  dessinés dans la texture de peau, crâne rasé) : humains v4 (`gen_human.py`, mêmes os et clips que la v3
  + clips `Dance`, `Dance2`, `Sit`, `Workout` ajoutés aussi à human_m/f/m2/f2 ; iris texturés, cils en carte).
  Tenues de plage et de soirée ordinaires, aucun contenu sexualisé, personnes inventées.
- `animal_dog`, `animal_cat`, `animal_bird` (mouette), `animal_parrot` (ara), `animal_crab` : animaux skinnés
  et animés (`gen_animals.py`), pelage / plumes / carapace en textures procédurales cuites avec normal maps
  (`nb_textures.animal_textures`).
- `prop_lifeguard_tower`, `prop_parasol`, `prop_towel`, `prop_dj_booth` (écran LED dessiné par le script),
  `prop_speaker_stack`, `prop_weights`, `prop_dumbbell`, `prop_rescue_tube` : décors plage / fête / cour de
  prison (`gen_scene_props.py`), sans marque ni logo.
- Chaque `<nom>.glb.js` est la copie base64 du `.glb` correspondant (secours hors serveur).
- `previews/*.png` : rendus d'aperçu (`render_previews.py`) ; planche des armes dans
  `tools/blender/previews/weapons_sheet.png` (`weapon_sheet.py`) ; planches humains v4, clips, animaux et
  décors dans `tools/blender/previews/{humans_v4,humans_clips,animals,props}_sheet.png` (`scene_sheets.py`).
