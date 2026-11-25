---
name: blender-assets
description: Pipeline Blender procédural (bpy 5.x, sans interface) qui génère les modèles 3D originaux de Néon Bay (voitures, humains animés, armes, mobilier urbain, monuments, équipements sportifs) en .glb pour three.js r128, avec copie base64 .glb.js, rendus d'aperçu et vérification Playwright. À utiliser dès qu'il faut régénérer, modifier, ajouter ou vérifier un modèle 3D du jeu (neon-bay/models), changer une couleur, une proportion, une animation ou un budget de polygones, ou diagnostiquer un .glb qui ne se charge pas ou dont les noms de matériaux/os/animations ne correspondent plus à ce que le jeu attend.
---

# Assets Blender de Néon Bay

Tous les modèles de `neon-bay/models/` (sauf `robot.glb`, CC0) sont **générés par du code** :
aucune géométrie importée, aucun asset d'un autre jeu, aucune arme réelle ni personne réelle
reconnaissable, aucune marque. On ne retouche jamais un .glb à la main :
on modifie le script puis on régénère.

## Régénérer

Depuis `neon-bay/` (Blender n'est pas nécessaire : le module `bpy` 5.3 est installé pour `python3`) :

```bash
python3 tools/blender/gen_cars.py            # v3 : car_sedan, car_sports, car_suv, car_van, car_police
python3 tools/blender/gen_cars.py sedan van  # seulement certaines
python3 tools/blender/gen_army.py            # army_jeep army_truck army_apc (args : jeep truck apc)
python3 tools/blender/vehicle_sheet.py       # planches véhicules (3/4 avant, 3/4 arrière, profil) :
                                             # tools/blender/previews/<nom>_sheet.png + vehicles_sheet.png
NB_VIEWS=front34,rear34,side,wheel,cabin,top python3 tools/blender/vehicle_sheet.py car_sedan  # vues de contrôle
python3 tools/blender/gen_props.py           # palm, lamp, hydrant, bench, traffic_light
python3 tools/blender/gen_landmarks.py       # lm_statue lm_palace prop_basket_hoop prop_basket_court prop_soccer_goal
                                             # prop_soccer_field prop_boxing_ring prop_ball_basket prop_ball_soccer
                                             # prop_stadium_stand + planches (args : ids ou noms courts, ex. "statue hoop")
python3 tools/blender/gen_landmarks.py --sheet [ids]   # planches seules : previews/landmarks_sheet.png, sport_sheet.png
NB_BACKFACE=1 python3 tools/blender/gen_landmarks.py --sheet   # faces arrière en rouge (contrôle des normales)
python3 tools/blender/gen_human.py           # les 9 humains (args "m" "f" "m2" "f2" "f3"...) ~6 s chacun, + expressions
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
| Voitures `car_*.glb` (v3) | **+X** | ~4,5 m hors tout (SUV 4,7, van 4,9) ; R roue 0,33 (sports 0,335, SUV 0,38, van 0,34) | matériaux `Paint` (carrosserie, recolorée par le jeu : tout nom contenant « paint »), `Glass` (transparent, alpha 0,55 : habitacle visible), `Tyre`, `Rim`, `LightFront` (émissif), `LightRear` (émissif), `Trim` : **7 matériaux max** ; roues = objets séparés `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR`, origine au moyeu, sans rotation : l'essieu est l'axe local Z (latéral), donc faire rouler = `wheel.rotation.z -= v*dt/R` ; enfants de `Body` ; maillages nommés `mesh_Wheel_*` (sinon les sous-maillages créés par three.js matchent aussi `/^Wheel/` et tournent deux fois) ; étriers dans `Body` (ne tournent pas). `car_police` : + `Livery` (2e couleur, non recolorée), nœud `Lightbar` (enfant de Body) avec `SirenRed` (côté gauche, −Z glTF) et `SirenBlue` (droit, +Z) émissifs ; ≤ 12 000 tris |
| Armée `army_*.glb` | **+X** | jeep 4,1 m, truck 7,4 m, apc 7,0 m ; R roue 0,38 / 0,55 / 0,55 | même contrat que les voitures (`Paint` olive mat — recolorée si le jeu passe une couleur —, `Glass`, `Tyre`, `Rim`, `LightFront`, `LightRear`, `Trim`, + `Canvas` pour la bâche du camion) ; roues : jeep `Wheel_FL/FR/RL/RR` ; truck + `Wheel_ML/MR` (essieu central) ; apc `Wheel_FL/FR`, `Wheel_F2L/F2R` (2e essieu), `Wheel_R2L/R2R` (3e), `Wheel_RL/RR` (4e, arrière) ; roues de secours = `SpareTyre` dans Body (pas animées) ; apc : nœud `Turret` (axe de tourelle, tourner = `rotation.y`) et son enfant `Gun` (axe des tourillons, pointer = `rotation.z`, + = vers le haut) ; ≤ 12 000 tris et ≤ 900 Ko |
| Humains `human_m/f/m2/f2.glb` (+ v4 f3 m3 f4 m4 m5) | **+Z** (glTF) | m 1,80 m / f et f2 1,71 m au crâne (1,82 / 1,72 avec les cheveux) ; m2 1,765 m (1,79 avec la casquette), pose A, semelles à y=0 | os `Hips Spine Chest Neck Head UpperArm.L/R LowerArm.L/R Hand.L/R UpperLeg.L/R LowerLeg.L/R Foot.L/R` + doigts (v3) `Thumb.L/R Thumb2.L/R` (pouce, enfants de Hand) et `Fingers.L/R Fingers2.L/R` (4 doigts : phalange proximale puis moyenne+distale) ; matériaux `Skin Shirt Pants Shoes Hair Eyes` (+ optionnels `Lips`, `EyeWhite`, jamais recolorés par le jeu ; + `Hat` casquette, **human_m2 seulement**, non recoloré par le jeu actuel) ; clips `Idle Walk Run Punch Death Aim AimRifle Crouch` + v4 `Dance Dance2 Sit Workout` ; textures 512×512 sur `Skin Shirt Pants Shoes` (+`Hat`), normal maps sur `Shirt Pants` (+`Hat`) ; < 9 000 triangles et < 900 Ko |
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

## Humains v4, animaux et décors de scène (plage, baile funk, prison)

```bash
python3 tools/blender/gen_human.py f3 m3 f4 m4 m5      # nouveaux humains (~10 s chacun) ; sans argument : les 9
python3 tools/blender/gen_animals.py [dog cat bird parrot crab]
python3 tools/blender/gen_scene_props.py [lifeguard_tower parasol towel dj_booth speaker_stack weights dumbbell rescue_tube]
python3 tools/blender/scene_sheets.py [humans_v4 humans_clips animals props]   # planches dans tools/blender/previews/
```

- **Humains v4** (`OUTFITS` en tête de `gen_human.py`, `Spec.top/bottom/feet/hair/hat/extras`) : mêmes os,
  mêmes noms, même prise d'arme que la v3. `human_f3` sauveteuse 1,70 m (Shirt = maillot une pièce rouge,
  Pants = short de bain, pieds nus + tongs `Shoes`, queue de cheval, lunettes `Gear`/`Lens` sur la tête,
  sifflet `Metal` sur cordon `Gear`) ; `human_m3` sauveteur 1,80 m (débardeur, short, tongs, bob = `Hat`) ;
  `human_f4` 1,68 m (crop top, jogging à bandes `Trim`, baskets montantes `Shoes` + semelles/lacets `Sole`,
  chignon, créoles et chaîne `Metal`) ; `human_m4` 1,78 m (maillot de foot à numéro « 10 » `Trim`, jogging,
  montantes, casquette `Hat`, chaîne) ; `human_m5` 1,81 m (combinaison orange = `Shirt` + `Pants` même
  couleur, tatouages dans la texture `Skin` via UV cylindriques des bras `armcyl`, crâne rasé). Nouveaux
  matériaux jamais recolorés : `Gear Metal Lens Trim Sole`. Visages v4 : iris texturé (`Eyes`, 64 px), ligne
  et carte de cils en `Hair`. Découpes de maillot/débardeur : couture « aimantée » sur une courbe lisse
  (`snap_boundary`) + passepoil (`seam_piping`) ; les bords de couture sont protégés à la décimation.
  Torse skinné par la hauteur (Hips → Spine → Chest) pour que haut et pantalon restent soudés en dansant.
- **Clips v4, sur les 9 humains** : `Dance` (2 s, 120 bpm, rebond des genoux, bassin, poings qui
  pompent), `Dance2` (2 s, ondulation du buste, bras au-dessus de la tête, appuis alternés), `Sit` (2 s,
  assis sur une marche de 0,46 m, avant-bras sur les cuisses), `Workout` (2 s, curls marteau alternés ;
  `prop_dumbbell` va dans la main). Tous bouclent.
- **Animaux** (`gen_animals.py`) : avant **+X** (comme `makeAnimal`), gauche vers −Z, métres, origine au sol.
  Matériaux `Fur` (recolorable), `Fur2` (poitrail, ventre, museau, chaussettes ; ailes ; dessous du crabe),
  `Eye` (+ fixes `Nose Beak Feet Tip Claw`). Clips : dog `Idle Walk Run Sit`, cat `Idle Walk Sit`,
  bird/parrot `Idle Fly` (ailes repliées en Idle par rotation + échelle 0,62 de `Wing2.*`), crab `Idle Walk`
  (marche de côté le long de ±Z glTF). Os : quadrupèdes `Hips Spine Chest Neck Head Ear.L/R Tail1-3
  UpperArm/LowerArm/Paw.L/R Thigh/Shin/Hock/HPaw.L/R` ; oiseaux `Body Neck Head Tail Wing1/Wing2.L/R
  Leg/Foot.L/R` ; crabe `Body Eye.L/R Claw1/Claw2/Pincer.L/R LegA0-3/LegB0-3.L/R`. ≤ 4 000 tris.
- **Décors** (`gen_scene_props.py`) : statiques, ≤ 3 000 tris, façade +Z ; `prop_dumbbell` (origine à la
  poignée) et `prop_rescue_tube` (origine au bout de la dragonne, tube le long de +X) sont tenus en main
  et dispensés du contrôle « posé au sol ». L'écran du DJ est une texture émissive dessinée en numpy.
- Contrôle (`check_glb_three.js`) : humains ≤ 1,15 Mo (v5) et 12 clips obligatoires ; contrat `animal`
  (Fur/Fur2/Eye, skinné, clips par espèce, ≤ 4 000 tris) ; contrat `sceneprop` pour les autres `prop_*`.
- Aperçus : vues `@chest` et `@waist` ajoutées à `render_previews.py` (coutures, ceintures).
- Limites connues : jupe de human_f2 étirée en `Sit` ; jonction cou/torse visible de près sur les hauts sans
  manches ; `Phong` (qualités basses) ignore la texture d'iris et l'écran LED (couleurs unies).

## Expressions du visage (v5 : shape keys → morph targets glTF)

```bash
python3 tools/blender/gen_human.py                 # les 9 humains, avec leurs 8 expressions
python3 tools/blender/face_sheet.py                # planche human_m + human_f : previews/faces_expressions_sheet.png
python3 tools/blender/face_sheet.py human_m4 human_f3      # autres personnages ; NB_FACE_VIEW=front, NB_FACE_OUT=...
```

- **Noms exacts** (valeurs 0..1) : `Blink Smile Angry Fear Surprise Sad MouthOpen JawClench` (`EXPRESSIONS`,
  réglages dans `EXPR` en tête du bloc « facial expressions » de `gen_human.py`, en mètres tête-locaux).
- **Maillage** : le visage est un 2e maillage skinné **`Face`** (même armature, os `Head`) : peau de la tête sous
  la calotte crânienne, sourcils, paupières, cils, lèvres, intérieur de bouche, yeux. Seul `Face` porte les morph
  targets ; `Body` n'en a aucun. Dans three.js, chaque primitive de `Face` est un `SkinnedMesh` (`Face_1` = Skin,
  `Face_2` Hair, `Face_3` Eyes, `Face_4` Lips, `Face_5` EyeWhite) avec le même `morphTargetDictionary` : régler
  l'influence sur **tous** les maillages qui ont ce dictionnaire. Raison : r128 agrandit la boîte englobante d'un
  maillage de la **somme** des deltas de ses morphs ; sur `Body` la taille du modèle (le jeu met à l'échelle par la
  hauteur) et le contrôle « pieds à y=0 » changeaient. La calotte (`split_head_top`, z tête > 0,05) reste dans
  `Body` (couture cachée sous les cheveux, épinglée : la peau ne bouge pas à moins de 1 cm de la couture).
- **Construction** (`face_keys`) : champs de déplacement lissés (sourcils + front, contour de l'œil, coins de la
  bouche, joues, menton, ailes du nez, masséters) appliqués à la peau **et** aux sourcils (ils suivent la peau) ;
  mâchoire = rotation autour d'une charnière (`JAW_PIVOT`) avec un poids nul sur le cou et la nuque ; la fente de la
  bouche est découpée dans la tête (`cut_mouth`, ellipse sous les lèvres) et donne sur une poche `Lips` + dents
  `EyeWhite` (`make_mouth_inside`) ; paupières = calottes `Skin` autour du globe (`make_lid`, entre deux grands
  cercles par les coins de l'œil) cachées au repos juste hors de la partie visible (`eye_open_range`) et qui
  tournent autour du centre de l'œil ; les cils suivent la paupière supérieure ; iris et globes ne bougent jamais.
- **Export** : `nb.export_glb(..., morph=True)` (`export_morph`, `export_morph_normal`, `export_apply=False`) puis
  `nb.compact_morph_targets` réécrit le .glb : deltas < 0,05 mm / normales < 0,015 mis à zéro (l'exportateur laisse
  du bruit sur toutes les normales), accesseurs **sparse** (sommets qui bougent seulement), positions en float32,
  normales en int8 normalisé (**`KHR_mesh_quantization` requis**, géré par GLTFLoader r128 ; ne pas quantifier les
  positions : Box3 r128 lirait les entiers bruts). ~110 Ko de morphs par humain. Les pièces non texturées ont des UV
  constants (avant : un carré 0..1 par face, qui dédoublait tous les sommets).
- **Dans le jeu** : r128 exige `material.morphTargets = true` et `morphNormals = true` ; GLTFLoader les pose et
  `material.clone()` les garde, mais un matériau recréé (Phong de `glbMat` en qualité basse) les perd : le visage
  reste neutre. Avec les normales, r128 n'applique que **4** influences non nulles à la fois.
- **Contrôle** : `check_glb_three.js` exige les 8 noms sur un `SkinnedMesh`, un déplacement ≥ 2 mm par cible,
  puis clone la scène avec `SkeletonUtils.clone`, vérifie que le clone a ses propres `morphTargetInfluences` et
  rend la tête du clone en WebGL (128 px) pour chaque expression : pixels changés affichés (ex. Blink ~60,
  Surprise ~1 700). Plafond humains : 1,15 Mo. Triangles : les paupières + bouche coûtent ~380 tris, rendus sur
  les vêtements / la calotte de cheveux des variantes les plus lourdes (`TRI_TRIM`).
- Limites : yeux très petits et blanc d'œil proche de la peau → « yeux écarquillés » (Fear, Surprise) peu
  lisibles, surtout portés par les sourcils et la bouche ; léger pli sur la joue quand la mâchoire s'ouvre ; les
  expressions se combinent par addition (Smile + MouthOpen marche, Angry + Surprise se contredit).

## Monuments et sport (`gen_landmarks.py`)

Lieux **inventés** (parodie) : rien de copié, aucun nom réel de monument dans les fichiers.
Échelle réelle, 1 unité = 1 m, Z-haut dans Blender, origine au sol au centre de l'emprise, « façade »
vers glTF +Z. Dans le jeu (1 m ≈ 30 unités) mettre l'échelle **30** à la main : le chargeur générique
(`loadModel`) calcule `scale = 55 / hauteur`, faux pour ces modèles.

| id | Contenu | Taille | Matériaux | tris / Ko |
|---|---|---|---|---|
| `lm_statue` | îlot (y=0 = niveau de l'eau, plateau à 2,5 m), ponton, fort en étoile à 7 branches, piédestal en granit, statue drapée : torche (`Glow`), couronne 5 rayons, tablette « NB », patine | flamme à 88,1 m ; îlot ~90 m (ponton vers +Z) ; statue `S_FIG` = 20 (silhouette de 1,8 → ~49 m), pieds à `Z_FEET` 39,3 m | Patina, PatinaDark, Glow, Gold, Stone, Grass, Rock, Wood, Shadow | ~10 850 / 440 |
| `lm_palace` | corps central + 2 ailes, portique 6 colonnes ioniques, fronton (médaillon + étoile dorée), 66 fenêtres à frontons, balustrades, toit en croupe, mât + drapeau (bleu néon, étoile rose), pelouse, allées, haies, grille + portail, fontaine | bâtiment 88 m, pelouse 110 × 80 m (dalle de 0,3 m sous y=0), drapeau ~30 m | Marble, Stone, Glass, Roof, Grass, Path, Hedge, Metal, Gold, Water, Wood, Flag, FlagStar, Glow | ~14 900 / 840 (budget 15 000 / 900) |
| `prop_basket_hoop` | panier sur pied mobile, panneau 1,8 × 1,05, cercle à 3,05 m, filet losanges (prismes fins) | emprise centrée ; centre du cercle à z = +1,24 m (glTF) | Metal, Padding, Board, Lines, HoopRed, Rope | 1 280 / 60 |
| `prop_basket_court` | dalle 32 × 19 m (terrain 28 × 15 + 2 m), lignes **dans la texture** 512 px | | CourtFloor (texture couleur, facteur blanc), Concrete | 24 / 85 |
| `prop_soccer_goal` | but 7,32 × 2,44 m, filet en brins | profondeur 2 m, centré | GoalPost, Metal, Rope | 1 136 / 58 |
| `prop_soccer_field` | dalle 96 × 62 m (terrain 90 × 56 + 3 m), bandes de tonte + lignes dans la texture | | Pitch, Concrete | 12 / 98 |
| `prop_boxing_ring` | ring 6,1 m entre poteaux, 4 cordes, coins rouge/bleu/blanc, marches, bandeau néon, 4 tours + portique à 7 m, 8 projecteurs | 12 × 12 × 7,3 m | Canvas, Skirt, Glow, Metal, CornerRed, CornerBlue, CornerWhite, Rope, Lens | 3 750 / 173 |
| `prop_ball_basket` / `prop_ball_soccer` | r 0,12 (normal map granuleuse, coutures en géométrie) / r 0,11 (32 panneaux bombés) | posés sur y=0 | Rubber, Seam / BallWhite, BallBlack | 1 800 / 106 ; 1 080 / 26 |
| `prop_stadium_stand` | module de 12 rangs, 192 sièges, allée centrale, rambardes | **x −5..5 exactement** : à répéter tous les 10 m le long de X | Concrete, SeatA/B/C, Metal | 6 670 / 305 |

Construction : `bake_textures()` cuit les textures **avant** `reset_scene()` (chaque cuisson remet la
scène à zéro) ; `finish()` joint les pièces en deux maillages, `<Nom>_Tex` (matériaux texturés, UV en
projection cubique à l'échelle `TILE`, ou planaires pour le terrain) et `<Nom>` sans UV (fichier plus
léger). Les pièces sont des solides fermés (`solid`, normales recalculées) ou des surfaces orientées à
la main (`surf`, `rev`, `strand`, `path_tube`) ; le lissage est posé par pièce et survit à la jointure.
Matériaux exportés en simple face. Statue : métaballes (`mb_elements`, rayons *visibles*) décimées à
6 200 tris + robe en révolution à plis (`robe_radius`). Leviers de budget du palais : espacement des
balustres (`balustrade(..., spacing)`, profil à 3 points), barreaux de la grille, nombre de fenêtres.
Pièges : un profil de `rev` doit aller de l'intérieur vers l'extérieur par le dessus (sinon normales
inversées ; vérifier avec `NB_BACKFACE=1`) ; en qualité Phong (moyenne/basse) le jeu ignore les
textures, donc les lignes des terrains disparaissent et `CourtFloor`/`Pitch` sont blancs (garder
`map: m.map` dans `glbMat` pour les voir) ; éviter dans les noms « paint », « glass », « rim », « trim »,
« metal » sauf voulu (le jeu change alors métal/rugosité).

## Budgets de polygones (triangles)

| Asset | Budget | Actuel (env.) |
|---|---|---|
| Voiture v3 (carrosserie + habitacle + 4 roues) | ≤ 9 000 tris, ≤ 700 Ko, ≤ 7 matériaux | 8 780–8 850 tris, 405–425 Ko |
| Police / armée | ≤ 12 000 tris, ≤ 900 Ko | police 10 330, jeep 7 700, truck 10 520, apc 9 350 ; 400–535 Ko |
| Humain (tout compris) | < 9 000 tris et ≤ 1,15 Mo (v5 : 12 clips + 8 expressions) | m 8 565 / f 8 995 / m2 8 405 / f2 8 841 / f3 8 961 / m3 8 741 / f4 8 958 / m4 8 842 / m5 8 632 tris ; 954–1 016 Ko |
| Animal | ≤ 4 000 | dog/cat 3 940, bird 3 250, parrot 3 430, crab 1 310 ; 200–340 Ko |
| Décor de scène `prop_*` (gen_scene_props) | ≤ 3 000 | 600–2 770 ; 20–100 Ko |
| Arme (v3) | pistol ≤ 4 000, fusils ≤ 9 000, lourdes (rocket, minigun, lmg, gl) ≤ 12 000 ; ≤ 600 Ko | 3 660–9 010 tris, 250–450 Ko (≈ 60 Ko de textures + ~50 o/tri) |
| Prop | ≤ ~1 500 | 450–1 100 |
| Total de tous les .glb | ~8,4 Mo depuis les armes v3 (armes : 3,75 Mo) | à surveiller (chargement mobile) |

Leviers : voitures → pas des sections du loft (`Car.section_xs`, `L / 0.22`), segments des roues
(`V.wheel(..., segs=18)` ; armée 16, apc 14), boulons (`beadlock`, `hub_nuts`), biseaux des petites
pièces (`bv=`) ; le script affiche `[vehicle] <nom>: N tris (budget), matériaux` ; humains → budgets par morceau (`budget = {"Shirt": ...}`
du corps, `decimate(head, 1900, head_keep)`, cheveux, mains `decimate(h, 430)`), nombre de
segments des bandes (`band(..., 14, ...)`) ; le script affiche `[human] parts: ...` avec le
compte de chaque morceau ; armes → côtés des tubes/lathes (`sides=`), biseaux (`bevel`, `seg`) ;
props → nombre de côtés des tubes/tours. `check_glb_three.js` échoue si un budget (triangles,
taille d'arme) est dépassé.

## Comment c'est construit (pour modifier)

- **Voitures v3** (`gen_cars.py` + kit commun `nb_vehicle.py`) : carrosserie = *loft* de
  sections à 14 points par demi-section (soubassement, bas de caisse, bas de caisse évasé,
  ligne de caractère, épaule, joint de vitre, vitre latérale, gouttière, pavillon), sans
  subdivision : profils `belt` / `roof` / `clear` / `width` en splines monotones (`pchip`) ; x des
  montants (`ws`, `rf`, `rr`, `rw`, `bpil`, `cpil`, `side_glass`), portes (`doors`), capot/coffre
  (`hood`, `trunk`, `tailgate`), arrondi des bouts (`nose`), évasement des passages de roue
  (`flare`), `cladding` (bas de caisse en Trim). Arêtes vives marquées sur la ligne de caractère,
  l'épaule et le bas de caisse. Matériau par bande : `band_material` (police : livrée bicolore).
  Détails posés sur la peau par lancer de rayons (`V.Surface`) : optiques = patchs conformes
  (`V.patch`, verre émissif + atlas réflecteurs / clignotant / recul), jours de portes, capot,
  coffre et pare-chocs = rubans (`V.seam`), calandre ajourée (cadre + lamelles + fond), prise
  d'air, plaques (`plate` : atlas `Rim`, sans texte lisible), rétros, poignées, essuie-glaces,
  antenne, échappements, diffuseur, doublures de passages de roue, étriers ; habitacle (`cabin` :
  bac inversé, planche de bord, volant, sièges) derrière `Glass` transparent. Jantes :
  `V.wheel(style=alloy5|sport|suv6|steel|army)`. Textures numpy (`V.vehicle_textures`, aucune
  cuisson) : sculptures + flancs du pneu (normal map, u autour de la roue), grain plastique
  `Trim`, tissage `Canvas`, atlas `LightFront` (u<0,5 phare, haut droit orange, bas droit blanc),
  LED `LightRear`, atlas `Rim` (v 0,76–0,99 = plaque). Nouvelle voiture = entrée dans `CARS`.
- **Armée** (`gen_army.py`) : pièces dures (`V.box`, `V.prism`, `V.loft` facetté + biseau),
  tubes (`V.tube` : arceaux, pare-buffle), numéros au pochoir à 7 segments (`V.stencil`, quads
  Trim, numéros inventés, lisibles des deux côtés via `stencil_side`), roue de secours
  (`spare`), jerrican, pelle, bâche en loft avec affaissement entre arceaux + doublure
  intérieure, coque d'APC (`apc_hull_section` + sections `glacis` / `nose` explicites : une
  section qui se recoupe donne une face noire), tourelle et canon en nœuds séparés.
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
