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
python3 tools/blender/gen_human.py           # human_m human_f human_m2 human_f2 (args "m" "f" "m2" "f2") ~10 s chacun
python3 tools/blender/gen_weapons.py         # w_pistol w_uzi w_shotgun w_rifle w_sniper w_rocket
                                             # w_minigun w_lmg w_gl w_rail  (args : ids, ex. "pistol rail")
python3 tools/blender/render_previews.py     # models/previews/<nom>.png pour chaque .glb
python3 tools/blender/weapon_sheet.py        # planche des armes : tools/blender/previews/weapons_sheet.png
python3 tools/blender/render_previews.py "human_m@AimRifle:0+w_rifle" human_f@face   # variantes
python3 tools/blender/render_previews.py "human_m@Aim:0/handR+w_pistol" human_m@far  # main en gros plan, vue à 10 m
node tools/blender/check_glb_three.js        # vérifie le chargement three.js r128 + contrats
```

Chaque script repart d'une scène vide (`bpy.ops.wm.read_factory_settings(use_empty=True)`), est
déterministe (graine fixe) et idempotent : relancer réécrit les mêmes fichiers. Chaque export
écrit `models/<nom>.glb` **et** `models/<nom>.glb.js`
(`window.NB_MODEL_DATA.<nom>='<base64>'`), la copie de secours que le jeu charge si le .glb
ne peut pas être servi (file://, Android). Ne jamais éditer le .glb.js à la main.

Fichiers : `tools/blender/nb_textures.py` (textures procédurales cuites des humains),
`tools/blender/nb_common.py` (scène, matériaux, maillages, lissage auto, application
des modificateurs sans `bpy.ops`, export glb + .glb.js), un `gen_*.py` par famille,
`render_previews.py`, `check_glb_three.js`.

## Contrats (le code du jeu en dépend, ne pas casser)

**Axes et échelle** : export toujours avec `export_yup=True`. Dans Blender on modélise en Z-haut ;
Blender +X → glTF +X, Blender +Z → glTF +Y, Blender −Y → glTF +Z. Unité = mètre. Origine au sol,
au centre de l'objet.

| Famille | Avant | Taille | Noms obligatoires |
|---|---|---|---|
| Voitures `car_*.glb` | **+X** | ~4,4 m de long (SUV 4,6, van 4,8) | matériaux `Paint` (carrosserie, recolorée par le jeu), `Glass`, `Tyre`, `Rim`, `LightFront` (émissif), `LightRear` (émissif), `Trim` ; roues = objets séparés `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR`, origine au moyeu, sans rotation : l'essieu est l'axe local Z (latéral), donc faire rouler = `wheel.rotation.z -= v*dt/R` ; enfants de `Body` |
| Humains `human_m/f/m2/f2.glb` | **+Z** (glTF) | m 1,80 m / f et f2 1,71 m au crâne (1,82 / 1,72 avec les cheveux) ; m2 1,765 m (1,79 avec la casquette), pose A, semelles à y=0 | os `Hips Spine Chest Neck Head UpperArm.L/R LowerArm.L/R Hand.L/R UpperLeg.L/R LowerLeg.L/R Foot.L/R` + doigts (v3) `Thumb.L/R Thumb2.L/R` (pouce, enfants de Hand) et `Fingers.L/R Fingers2.L/R` (4 doigts : phalange proximale puis moyenne+distale) ; matériaux `Skin Shirt Pants Shoes Hair Eyes` (+ optionnels `Lips`, `EyeWhite`, jamais recolorés par le jeu ; + `Hat` casquette, **human_m2 seulement**, non recoloré par le jeu actuel) ; clips `Idle Walk Run Punch Death Aim AimRifle Crouch` ; textures 512×512 sur `Skin Shirt Pants Shoes` (+`Hat`), normal maps sur `Shirt Pants` (+`Hat`) ; < 9 000 triangles et < 900 Ko |
| Armes `w_<id>.glb` | canon **+X**, haut **+Y**, côté droit +Z | réelle : pistol 0,23 m, uzi 0,47, shotgun 1,04, rifle 0,94, sniper 1,25, rocket 1,13, minigun 1,01, lmg 1,06, gl 0,77, rail 1,02 | origine = centre de la poignée (main droite ; poignée arrière pour rocket/minigun) ; matériaux `Body` (couleur principale, recolorée pour les peintures : le jeu recolore tout matériau dont le nom contient « body », n'en créer aucun autre), `Metal`, `Grip`, `Glow` (émissif : points de visée, LED, bobines du rail) sur toutes, `Lens` (optiques) sur rifle, sniper, rocket, gl, rail ; v3 ajoute `MetalEdge` (usure claire des arêtes) et `Polymer` ; UV + textures 256 px ; un seul maillage, pas d'animation |
| Lampadaire `lamp.glb` | bras vers +Z | 6 m | matériau émissif `Bulb` (+ `Metal`) |
| Autres props | façade vers +Z | réelle | `palm` (Trunk/Leaves/Coconut), `hydrant` (HydrantPaint/Metal), `bench` (Wood/Metal), `traffic_light` (Metal/Housing/LightRed/LightYellow/LightGreen) |

Variantes : `human_m2` = silhouette trapue (1,765 m, épaules/torse/membres plus larges, ventre),
sweat à capuche (slot `Shirt` : manches longues + poignets, capuche posée sur les épaules, poche
kangourou, cordons ; ourlet bas à la place de la ceinture), jean `Pants`, baskets `Shoes`,
casquette (slot `Hat`, tête) ; `human_f2` = haut ajusté (`Shirt`), **jupe = slot `Pants`**
(+ ceinture de jupe, short `Pants` caché dessous), jambes nues (`Skin`), ballerines `Shoes`,
cheveux tirés en **queue de cheval** (mèches en tubes, élastique en `Shirt`). Mêmes os, mêmes
clips, même prise d'arme que human_m/f.

Textures (v3) : `nb_textures.py` construit des graphes de nœuds procéduraux (bruits 4D
« torus » pour que ça boucle, motifs périodiques), les cuit en Cycles (bake EMIT) sur un plan
1×1, puis écrit des PNG optimisés (normal maps dérivées de la hauteur cuite, repliée sur sa
période : boucle exacte et ~3 Ko). Elles sont **en gris clair quasi neutre** (moyenne ~0,9) et
le .glb exporte `baseColorFactor × baseColorTexture` : le jeu garde la couleur via
`material.color`. `skin_m/f` (RGB : u 0–0,25 = bande « peau simple » bras/mains/jambes,
u 0,25–1 = projection de face de la tête : rougeurs joues/nez/oreilles, cernes légers, ombre
de barbe pour l'homme, pores), `jersey` (+`_n`, maille du t-shirt/sweat, tuile 5 cm),
`denim` (+`_n`, sergé + flammes verticales, tuile 6 cm ; aussi la casquette), `shoes`
(v 0,32–1 grain du cuir pour dessus/ceinture, v 0–0,26 flanc de semelle à rainures). Les UV
sont posés par morceau avant la jointure (`o["uv"]` → `assign_uvs` : `box:<slot>` projection
cubique à l'échelle réelle, `face`, `strip`, `shoe`, `sole`, `belt`). Le jeu en qualité
« high » garde les cartes (clone du matériau standard) ; en Phong (qualités inférieures) elles
sont ignorées, sans erreur. Budget : ~210 Ko de PNG par humain.

Doigts (v3) : `Spec._hand` calcule repère de main et articulations ; `fingers(p, côté, f1, f2,
t1, t2, opp)` pose les doigts (degrés, + = vers la paume). Préréglages : `HAND_RELAXED`
(tous les clips sauf ci-dessous, ajouté automatiquement), `HAND_GRIP` (main droite d'Aim et
AimRifle, refermée sur la poignée), `HAND_SUPPORT` (main gauche d'AimRifle sous le
garde-main), `HAND_FIST` (Punch). Le jeu en visée mobile (`aimArms`) remet HandR à l'identité
mais pas les doigts : ils gardent alors la pose du clip en cours (détendue).

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
(2 s, deux mains, crosse au creux de l'épaule droite, main gauche sous le garde-main ~0,28 m
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
`AimRifle` `(-0.3471, -0.164, 0.8898, 0.2467)` (mêmes valeurs pour human_m, f, m2 et f2, inchangées en v3 ;
recalculées à chaque check). Dans le jeu, diviser la position par l'échelle appliquée au modèle
si l'arme est mise à l'échelle séparément.

## Budgets de polygones (triangles)

| Asset | Budget | Actuel (env.) |
|---|---|---|
| Voiture (carrosserie + 4 roues) | ≤ ~4 000 | 3 600–3 800 |
| Humain (tout compris) | < 9 000 tris et < 900 Ko | m 8 190 / f 8 620 / m2 8 030 / f2 8 740 tris ; 838 / 854 / 799 / 876 Ko (dont ~210 Ko de textures) |
| Arme (v3) | pistol ≤ 4 000, fusils ≤ 9 000, lourdes (rocket, minigun, lmg, gl) ≤ 12 000 ; ≤ 600 Ko | 3 660–9 010 tris, 250–450 Ko (≈ 60 Ko de textures + ~50 o/tri) |
| Prop | ≤ ~1 500 | 450–1 100 |
| Total de tous les .glb | ~8,4 Mo depuis les armes v3 (armes : 3,75 Mo) | à surveiller (chargement mobile) |

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
  `sp.sleeve_t`, plan d'ourlet `sp.hem` ; variantes : `Spec(female, "2")` → `sp.stocky` / `sp.dress`), puis le corps est séparé par matériau et chaque
  morceau décimé (les coutures deviennent des bords, préservés). Volume des vêtements : bandes
  posées par lancer de rayons (`band`, `band_from_points`) : col sur la ligne exacte où le cou
  sort du t-shirt (`neckline`), ourlets de manches, ceinture + boucle + passants, ourlets de
  pantalon ; semelles = dalle extrudée du contour de la chaussure. Cheveux : calotte copiée du
  cuir chevelu dense (`scalp()` = ligne frontale, golfes temporaux, pattes, contour d'oreilles),
  ligne lissée et reprojetée, épaisseur variable (plus haute sur le dessus, mèches) qui
  s'amincit sur 7 anneaux ; la femme ajoute des volumes (carré long jusqu'aux épaules, frange
  balayée, pointes) avec une métaballe négative qui dégage le visage. v3 : mèches en géométrie
  (`strand_ridge` module l'épaisseur selon le sens des cheveux : depuis la couronne pour
  l'homme, en chute pour le carré, vers l'élastique pour la queue de cheval), arcades et
  sourcils plus marqués, ligne de cils sombre (`lash_line`, matériau Eyes), plancher de
  mâchoire + creux sous le menton (ombre sous le menton vue de dessus / 3/4). Accessoires
  v3 : `make_cap`, `trim_under_cap`, `make_pocket`, `make_drawstrings`, `make_skirt` (poids :
  Hips en haut → jambe de son côté vers l'ourlet), `make_ponytail`. Sourcils = lamelles
  posées sur l'arcade, lèvres = tubes effilés posés sur la bouche (`make_lips`), yeux = sphère
  `EyeWhite` + iris `Eyes`. Les poids de peau viennent du même champ implicite (articulations
  douces) ; cheveux/yeux → `Head` (cheveux longs : mélange Neck/Chest sous la nuque), col →
  Chest/Neck seulement. Les animations sont des fonctions `t ∈ [0,1] → pose` (`idle_pose`,
  `walk_pose`, `run_pose`, `aim_pose`, `aim_rifle_pose`, `crouch_pose`, ...).
- **Armes** (`gen_weapons.py`, version 3 « vitrine ») : profils latéraux extrudés (`prism`),
  sections extrudées le long de X (`xsec`, `chamfer_sec`), tubes/tours/anneaux (`tube_x`, `lathe_x`,
  `ring_x`, `fluted_x`), **découpes booléennes** EXACT appliquées sans `bpy.ops` (`cut(obj, cutters,
  pre=(largeur, seg))` : biseauter avant de découper coûte bien moins de triangles ; `slot_cutter`,
  `cutter`, `cutter_prism`, `cutter_cyl`, `ring_cutter`), puis Bevel dont les nouvelles faces prennent
  `MetalEdge` (`edge=True`, défaut pour `Metal`). Kits : `picatinny`, `screw`/`screw_z`, `pin_y`,
  `sling_loop`, `knurl_*`, `trigger_group`, `pistol_grip` (même centre qu'en v2 : ne pas changer ses
  arguments, sinon la prise de main bouge), `muzzle_brake`, `slotted_handguard`, `red_dot`, `scope`,
  `ring_mount`, `flip_sight`, `curved_mag`. `finish_weapon()` place l'origine sur la poignée, lisse et
  pose des UV en projection cubique à l'échelle (`WEAPON_TILE`). Textures : `nb_textures.weapon_textures()`
  (`poly`, `poly_n`, `checker_n`, `steel`). `NB_DEBUG=1` affiche les pièces les plus lourdes ; le
  script affiche tris/budget (`BUDGET`). Pièges : un `slot_cutter` plus haut que long était dégénéré
  (corrigé) ; des découpeurs qui se chevauchent exigent `use_self` (activé) ; les grosses découpes +
  biseau après coup explosent le budget. Planche : `python3 tools/blender/weapon_sheet.py [ids]` →
  `tools/blender/previews/weapons_sheet.png` (profil orthographique + 3/4, fond sombre ; regarder
  la planche avec Read et chercher les pièces flottantes). Designs génériques inventés, sans marquage.
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
dans la main droite, même règle de poigne que le check), `human_m@Aim:0/handR+w_pistol` (vue
après « / » : `handR`, `handL`, `face`, `far`, `top`), `@far` / `@top` (corps entier à 10 m,
lecture en jeu). `NB_PREVIEW_VIEW=side|front|back` force la
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
- Les textures des humains sont des PNG emballés : le bruit coûte cher en PNG. Garder les
  motifs à période entière en pixels (32 ou 64 répétitions sur 512) et quantifier (`levels`) ;
  `check_glb_three.js` échoue au-delà de 900 Ko par humain.
- Contrôle : hauteur attendue selon le préfixe (`human_f*` 1,66–1,76 m, sinon 1,75–1,85 m),
  textures 512×512 sur Skin/Shirt/Pants/Shoes, normal maps sur Shirt/Pants, os des doigts,
  `Hat` pour human_m2.
