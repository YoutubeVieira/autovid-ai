---
name: blender-assets
description: Pipeline Blender procédural (bpy 5.x, sans interface) qui génère les modèles 3D originaux de Néon Bay (voitures, humains animés, armes, mobilier urbain) en .glb pour three.js r128, avec copie base64 .glb.js, rendus d'aperçu et vérification Playwright. À utiliser dès qu'il faut régénérer, modifier, ajouter ou vérifier un modèle 3D du jeu (neon-bay/models), changer une couleur, une proportion, une animation ou un budget de polygones, ou diagnostiquer un .glb qui ne se charge pas ou dont les noms de matériaux/os/animations ne correspondent plus à ce que le jeu attend.
---

# Assets Blender de Néon Bay

Tous les modèles de `neon-bay/models/` (sauf `robot.glb`, CC0) sont **générés par du code** :
aucune géométrie importée, aucun asset d'un autre jeu, aucune arme réelle ni personne réelle
reconnaissable, aucune marque. On ne retouche jamais un .glb à la main :
on modifie le script puis on régénère.

## Régénérer

Depuis `neon-bay/` (Blender n'est pas nécessaire : le module `bpy` 5.3 est installé pour `python3`) :

```bash
python3 tools/blender/gen_cars.py            # car_sedan, car_sports, car_suv, car_van
python3 tools/blender/gen_cars.py sedan van  # seulement certaines
python3 tools/blender/gen_props.py           # palm, lamp, hydrant, bench, traffic_light
python3 tools/blender/gen_human.py           # human_m + human_f   (arg "m" ou "f" pour un seul) ~5 s
python3 tools/blender/gen_weapons.py         # w_pistol w_uzi w_shotgun w_rifle w_sniper w_rocket
                                             # w_minigun w_lmg w_gl w_rail  (args : ids, ex. "pistol rail")
python3 tools/blender/render_previews.py     # models/previews/<nom>.png pour chaque .glb
python3 tools/blender/render_previews.py "human_m@AimRifle:0+w_rifle" human_f@face   # variantes
node tools/blender/check_glb_three.js        # vérifie le chargement three.js r128 + contrats
```

Chaque script repart d'une scène vide (`bpy.ops.wm.read_factory_settings(use_empty=True)`), est
déterministe (graine fixe) et idempotent : relancer réécrit les mêmes fichiers. Chaque export
écrit `models/<nom>.glb` **et** `models/<nom>.glb.js`
(`window.NB_MODEL_DATA.<nom>='<base64>'`), la copie de secours que le jeu charge si le .glb
ne peut pas être servi (file://, Android). Ne jamais éditer le .glb.js à la main.

Fichiers : `tools/blender/nb_common.py` (scène, matériaux, maillages, lissage auto, application
des modificateurs sans `bpy.ops`, export glb + .glb.js), un `gen_*.py` par famille,
`render_previews.py`, `check_glb_three.js`.

## Contrats (le code du jeu en dépend, ne pas casser)

**Axes et échelle** : export toujours avec `export_yup=True`. Dans Blender on modélise en Z-haut ;
Blender +X → glTF +X, Blender +Z → glTF +Y, Blender −Y → glTF +Z. Unité = mètre. Origine au sol,
au centre de l'objet.

| Famille | Avant | Taille | Noms obligatoires |
|---|---|---|---|
| Voitures `car_*.glb` | **+X** | ~4,4 m de long (SUV 4,6, van 4,8) | matériaux `Paint` (carrosserie, recolorée par le jeu), `Glass`, `Tyre`, `Rim`, `LightFront` (émissif), `LightRear` (émissif), `Trim` ; roues = objets séparés `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR`, origine au moyeu, sans rotation : l'essieu est l'axe local Z (latéral), donc faire rouler = `wheel.rotation.z -= v*dt/R` ; enfants de `Body` |
| Humains `human_m/f.glb` | **+Z** (glTF) | 1,80 m / 1,71 m au crâne (1,815 / 1,73 avec les cheveux), pose A, semelles à y=0 | os `Hips Spine Chest Neck Head UpperArm.L/R LowerArm.L/R Hand.L/R UpperLeg.L/R LowerLeg.L/R Foot.L/R` ; matériaux `Skin Shirt Pants Shoes Hair Eyes` (+ optionnels `Lips` lèvres, `EyeWhite` blanc de l'œil, jamais recolorés par le jeu) ; clips `Idle Walk Run Punch Death Aim AimRifle Crouch` |
| Armes `w_<id>.glb` | canon **+X**, haut **+Y**, côté droit +Z | réelle : pistol 0,23 m, uzi 0,47, shotgun 1,04, rifle 0,94, sniper 1,25, rocket 1,13, minigun 1,01, lmg 1,06, gl 0,77, rail 1,02 | origine = centre de la poignée (main droite ; poignée arrière pour rocket/minigun) ; matériaux `Body` (couleur principale, recolorée pour les peintures), `Metal`, `Grip`, `Glow` (émissif : points de visée, LED, bobines du rail) sur toutes, `Lens` (optiques) sur rifle, sniper, rocket, gl, rail ; un seul maillage, pas d'animation |
| Lampadaire `lamp.glb` | bras vers +Z | 6 m | matériau émissif `Bulb` (+ `Metal`) |
| Autres props | façade vers +Z | réelle | `palm` (Trunk/Leaves/Coconut), `hydrant` (HydrantPaint/Metal), `bench` (Wood/Metal), `traffic_light` (Metal/Housing/LightRed/LightYellow/LightGreen) |

Attention : three.js (`PropertyBinding.sanitizeNodeName`) **supprime les points** des noms de
nœuds : dans le jeu les os s'appellent `UpperArmL`, `HandR`, etc. Les noms de matériaux, eux,
sont conservés tels quels.

Animations humaines : 24 i/s, une action Blender par clip, poussée dans une piste NLA, export
`export_animation_mode="ACTIONS"` → 8 `AnimationClip` dans `gltf.animations`, toutes en place
(pas de déplacement racine). Bouclent (dernière clé = première, vérifié par le check) :
`Idle` (2 s), `Walk` (1 s, foulée ~1 m/s à vitesse 1 : attaque talon, déroulé, poussée sur
l'avant-pied, bassin qui monte/descend et tourne, bras en balancier opposé), `Run` (0,67 s,
phase de vol, talon qui remonte, coudes ~90°), `Aim` (2 s, debout, bras droit tendu devant à
hauteur d'épaule, buste légèrement de profil, bras gauche détendu, respiration), `AimRifle`
(2 s, deux mains, crosse au creux de l'épaule droite, main gauche sous le garde-main ~0,29 m
devant la droite, joue inclinée), `Crouch` (2 s, accroupi bas : pied gauche à plat devant,
genou droit près du sol sur la pointe du pied, buste penché). Ne bouclent pas : `Punch`
(0,67 s, part de la garde et y revient) et `Death` (1,5 s, finit allongé, à jouer en
`LoopOnce` + `clampWhenFinished`).

Les poses s'écrivent en degrés dans les axes de l'armature (`pitch` autour de X : négatif =
vers l'avant pour un membre pendant, positif = plier le genou ; `out` autour de Y ; `yaw`
autour de Z), relatives au parent, ou directement en matrice 3×3 (même convention) ; elles
sont converties dans le repère de chaque os par `pose_quat()` : on peut donc changer les rolls
sans casser les animations. Walk, Run, Idle, Aim, AimRifle et Crouch posent les pieds par
**IK à deux os** (`leg_ik` : position de cheville calculée depuis un pied « à plat » + angle
de pied qui pivote sur le talon ou l'avant-pied, `foot_target`) et les bras d'Aim/AimRifle par
`arm_ik` (cible de poignet + direction de la main et du pouce), avec une cinématique directe
maison (`fk`) identique à celle de Blender.

**Tenir une arme** (calculé et affiché par `check_glb_three.js`) : attacher `w_<id>` comme
enfant de l'os `HandR` ; l'axe local +Y de `HandR` suit la main (poignet → doigts). Point de
poigne dans le repère de l'os : `(0.016, 0.078, -0.007)` (7,8 cm le long de la main, 1,8 cm
vers la paume). Rotation locale pour que le canon pointe vers l'avant du personnage (+Z) et
le haut vers +Y, à t=0 : `Aim` quaternion (x,y,z,w) `(-0.3496, -0.348, 0.6307, 0.5991)`,
`AimRifle` `(-0.3471, -0.164, 0.8898, 0.2467)` (mêmes valeurs pour human_m et human_f ;
recalculées à chaque check). Dans le jeu, diviser la position par l'échelle appliquée au modèle
si l'arme est mise à l'échelle séparément.

## Budgets de polygones (triangles)

| Asset | Budget | Actuel (env.) |
|---|---|---|
| Voiture (carrosserie + 4 roues) | ≤ ~4 000 | 3 600–3 800 |
| Humain (tout compris) | < 9 000 | m 8 100 / f 8 600 (~425–440 Ko avec 8 clips) |
| Arme | < 2 500 et < 120 Ko | 900–2 050 tris, 39–75 Ko |
| Prop | ≤ ~1 500 | 450–1 100 |
| Total de tous les .glb | ≤ ~3 Mo | ~1,9 Mo |

Leviers : voitures → nombre de sections du loft (`build_body`), segments des roues (`lathe(...,
14)`), biseaux des petites pièces ; humains → budgets par morceau (`budget = {"Shirt": ...}`
du corps, `decimate(head, 1900, head_keep)`, cheveux, mains `decimate(h, 430)`), nombre de
segments des bandes (`band(..., 14, ...)`) ; le script affiche `[human] parts: ...` avec le
compte de chaque morceau ; armes → côtés des tubes/lathes (`sides=`), biseaux (`bevel`, `seg`) ;
props → nombre de côtés des tubes/tours. `check_glb_three.js` échoue si un budget (triangles,
taille d'arme) est dépassé.

## Comment c'est construit (pour modifier)

- **Voitures** (`gen_cars.py`) : la carrosserie est un *loft* de sections à 12 points le long de
  X ; chaque type est un dictionnaire de profils (`belt` = ligne de caisse, `roof`, `clear` =
  garde au sol, `width`) indexés par x en mètres, plus les x des montants (`ws` pare-brise,
  `rf`/`rr` pavillon, `rw` lunette, `bpil` montant B). Les passages de roue sont creusés dans le
  profil bas. Vitres, montants et soubassement sont des bandes de matériaux du même maillage ;
  plis (crease) sur la ligne de caisse et les contours de vitres, subdivision 1 appliquée, lissage
  auto. Phares, feux, calandre, pare-chocs, rétros et poignées sont posés par lancer de rayon
  sur la carrosserie. Nouvelle voiture = nouvelle entrée dans `CARS`.
- **Humains** (`gen_human.py`, version 2) : quatre familles de métaballes séparées (noms
  différents → pas de fusion entre elles), chacune polygonisée à sa résolution puis décimée à
  son budget : corps (`body_elements`, ~8 mm : torse, bras, jambes de pantalon, chaussures),
  tête (`head_elements`, ~4 mm : crâne, mâchoire, pommettes, arcades, orbites en métaballes
  **négatives**, nez avec ailes et narines, bouche, menton, oreilles avec creux, cou), mains
  (`hand_elements`, ~3,4 mm, une famille par main : paume, 4 doigts légèrement fléchis, pouce
  séparé), cheveux. Chaque élément porte son os et sa zone de vêtement ; `classify()` donne les
  matériaux avant décimation (ourlets droits : plan de ceinture `sp.waist`, plan de manche
  `sp.sleeve_t`, plan d'ourlet `sp.hem`), puis le corps est séparé par matériau et chaque
  morceau décimé (les coutures deviennent des bords, préservés). Volume des vêtements : bandes
  posées par lancer de rayons (`band`, `band_from_points`) : col sur la ligne exacte où le cou
  sort du t-shirt (`neckline`), ourlets de manches, ceinture + boucle + passants, ourlets de
  pantalon ; semelles = dalle extrudée du contour de la chaussure. Cheveux : calotte copiée du
  cuir chevelu dense (`scalp()` = ligne frontale, golfes temporaux, pattes, contour d'oreilles),
  ligne lissée et reprojetée, épaisseur variable (plus haute sur le dessus, mèches) qui
  s'amincit sur 7 anneaux ; la femme ajoute des volumes (carré long jusqu'aux épaules, frange
  balayée, pointes) avec une métaballe négative qui dégage le visage. Sourcils = lamelles
  posées sur l'arcade, lèvres = tubes effilés posés sur la bouche (`make_lips`), yeux = sphère
  `EyeWhite` + iris `Eyes`. Les poids de peau viennent du même champ implicite (articulations
  douces) ; cheveux/yeux → `Head` (cheveux longs : mélange Neck/Chest sous la nuque), col →
  Chest/Neck seulement. Les animations sont des fonctions `t ∈ [0,1] → pose` (`idle_pose`,
  `walk_pose`, `run_pose`, `aim_pose`, `aim_rifle_pose`, `crouch_pose`, ...).
- **Armes** (`gen_weapons.py`) : surtout des profils latéraux (x, z) extrudés en épaisseur
  (`prism`), des tubes et tours le long de X (`tube_x`, `lathe_x`, `ring_x`), petits chanfreins
  (modificateur Bevel appliqué) pour accrocher la lumière de loin ; `pistol_grip()` renvoie le
  centre de la poignée et `finish_weapon()` y place l'origine. Designs génériques inventés.
- **Props** (`gen_props.py`) : tours (`lathe_obj`), tubes balayés (`tube`), boîtes biseautées.

## Ajouter un nouvel asset

1. Choisir le script de la famille (ou en créer un `tools/blender/gen_<famille>.py` en copiant
   l'en-tête : `sys.path.insert` + `import bpy` **avant** `bmesh`/`mathutils` + `import nb_common as nb`).
2. Écrire une fonction `make_<nom>()` qui crée les objets avec `nb.material("NomContrat", ...)`,
   `nb.box`, `nb.cylinder`, `nb.lathe`, `tube`, puis `nb.join(parts, "Nom")` et `nb.auto_smooth`.
   Modéliser en Z-haut, origine au sol, avant selon le tableau ci-dessus.
3. L'enregistrer dans le dictionnaire (`PROPS`, `CARS`, ...) et appeler `nb.export_glb("<nom>")`
   (`animations=True` pour un modèle armé) : cela écrit aussi le `.glb.js`.
4. Ajouter son contrat (matériaux, nœuds, budget) dans `CONTRACT` de `check_glb_three.js`,
   lancer la vérification, puis `render_previews.py <nom>` et regarder l'image.
5. Déclarer le modèle côté jeu (`js/data.js`, `MODELS`) — c'est du code de jeu, à coordonner
   avec la personne qui l'intègre — et l'ajouter à `models/CREDITS.md`.

## Aperçus

`python3 tools/blender/render_previews.py [noms...]` importe chaque .glb, le cadre en vue 3/4
(caméra ajustée à la boîte englobante ; armes vues de leur côté droit), éclairage studio 3
lumières + sol, 640×400, et écrit `models/previews/<nom>.png`. Les humains sont posés à
l'image 1 de `Idle`. Variantes : `human_m@Walk:6` (clip + image), `human_f@face` (gros plan
tête ; `@front`, `@side`, `@feet`, `@hands` pour déboguer), `human_m@AimRifle:0+w_rifle` (arme
dans la main droite, même règle de poigne que le check). `NB_PREVIEW_VIEW=side|front` force la
caméra, `NB_PREVIEW_OUT=<dossier>` écrit ailleurs (aperçus de travail), `NB_SAMPLES=8` accélère. Sans écran, Eevee
plante (pas d'EGL/Vulkan) : le script passe donc automatiquement en **Cycles CPU, 32 échantillons,
débruitage OIDN** (~6 s par image). Forcer un moteur avec `NB_RENDER_ENGINE=CYCLES` ou
`BLENDER_EEVEE`.

## Pièges connus

- `import bmesh` avant `import bpy` → `ModuleNotFoundError` avec le module bpy.
- Pas de `bpy.ops` dépendant d'une fenêtre : utiliser `nb.apply_modifiers` (via
  `new_from_object`) et `nb.join` ; le lissage auto 4.1+ est fait à la main (`nb.auto_smooth`).
- Draco / meshopt ne sont pas disponibles dans ce bpy : ne pas activer la compression.
- Si un clip manque dans three.js : vérifier que chaque action a une piste NLA et
  `export_animation_mode="ACTIONS"`.
- Métaballes : deux objets dont les noms ne diffèrent que par un suffixe `.001` fusionnent
  (même famille) ; garder des noms distincts (`BodyMB`, `HeadMB`, `HandLMB`...).
- Décimation « Collapse » avec groupe de sommets : si le groupe protège trop, le résultat
  dépasse la cible ; `decimate()` refait alors une passe sans groupe.
- Les zones de couture entre matériaux sont en escalier sur le maillage dense : elles sont
  cachées par les bandes (col, manches, ceinture, ourlets) ; garder une bande sur toute
  nouvelle couture visible.
- Le jeu reconstruit les matériaux en Phong (`glbMat`) sans couleurs de sommets : ne pas
  coder de couleur dans les sommets, utiliser un matériau nommé.
