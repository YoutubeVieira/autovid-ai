---
name: blender-assets
description: Pipeline Blender procédural (bpy 5.x, sans interface) qui génère les modèles 3D originaux de Néon Bay (voitures, humains animés, mobilier urbain) en .glb pour three.js r128, avec copie base64 .glb.js, rendus d'aperçu et vérification Playwright. À utiliser dès qu'il faut régénérer, modifier, ajouter ou vérifier un modèle 3D du jeu (neon-bay/models), changer une couleur, une proportion, une animation ou un budget de polygones, ou diagnostiquer un .glb qui ne se charge pas ou dont les noms de matériaux/os/animations ne correspondent plus à ce que le jeu attend.
---

# Assets Blender de Néon Bay

Tous les modèles de `neon-bay/models/` (sauf `robot.glb`, CC0) sont **générés par du code** :
aucune géométrie importée, aucun asset d'un autre jeu. On ne retouche jamais un .glb à la main :
on modifie le script puis on régénère.

## Régénérer

Depuis `neon-bay/` (Blender n'est pas nécessaire : le module `bpy` 5.3 est installé pour `python3`) :

```bash
python3 tools/blender/gen_cars.py            # car_sedan, car_sports, car_suv, car_van
python3 tools/blender/gen_cars.py sedan van  # seulement certaines
python3 tools/blender/gen_props.py           # palm, lamp, hydrant, bench, traffic_light
python3 tools/blender/gen_human.py           # human_m + human_f   (arg "m" ou "f" pour un seul)
python3 tools/blender/render_previews.py     # models/previews/<nom>.png pour chaque .glb
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
| Humains `human_m/f.glb` | **+Z** (glTF) | 1,80 m / 1,70 m, pose A | os `Hips Spine Chest Neck Head UpperArm.L/R LowerArm.L/R Hand.L/R UpperLeg.L/R LowerLeg.L/R Foot.L/R` ; matériaux `Skin Shirt Pants Shoes Hair` (+ `Eyes`) ; clips `Idle Walk Run Punch Death` |
| Lampadaire `lamp.glb` | bras vers +Z | 6 m | matériau émissif `Bulb` (+ `Metal`) |
| Autres props | façade vers +Z | réelle | `palm` (Trunk/Leaves/Coconut), `hydrant` (HydrantPaint/Metal), `bench` (Wood/Metal), `traffic_light` (Metal/Housing/LightRed/LightYellow/LightGreen) |

Attention : three.js (`PropertyBinding.sanitizeNodeName`) **supprime les points** des noms de
nœuds : dans le jeu les os s'appellent `UpperArmL`, `HandR`, etc. Les noms de matériaux, eux,
sont conservés tels quels.

Animations humaines : 24 i/s, une action Blender par clip, poussée dans une piste NLA, export
`export_animation_mode="ACTIONS"` → 5 `AnimationClip` dans `gltf.animations`. `Idle` (2 s),
`Walk` (1 s), `Run` (0,67 s) bouclent (dernière clé = première) ; `Punch` (0,67 s, part de la
garde et y revient) et `Death` (1,5 s, finit allongé, à jouer en `LoopOnce` +
`clampWhenFinished`) ne bouclent pas. Les poses s'écrivent en degrés dans les axes de
l'armature (`pitch` autour de X : négatif = vers l'avant pour un membre pendant, positif =
plier le genou ; `out` autour de Y ; `yaw` autour de Z) et sont converties dans le repère de
chaque os par `pose_quat()` : on peut donc changer les rolls sans casser les animations.

## Budgets de polygones (triangles)

| Asset | Budget | Actuel (env.) |
|---|---|---|
| Voiture (carrosserie + 4 roues) | ≤ ~4 000 | 3 600–3 800 |
| Humain (corps + cheveux + yeux) | ≤ ~6 000 | 5 500–5 900 |
| Prop | ≤ ~1 500 | 450–1 100 |
| Total de tous les .glb | ≤ ~3 Mo | ~1 Mo |

Leviers : voitures → nombre de sections du loft (`build_body`), segments des roues (`lathe(...,
14)`), biseaux des petites pièces ; humains → cible du Decimate (`m.ratio = 4900 / ...`), poids
du groupe `Detail` (tête et mains gardent plus de triangles), `decimate(hair, ...)` ; props →
nombre de côtés des tubes/tours. `check_glb_three.js` échoue si un budget est dépassé.

## Comment c'est construit (pour modifier)

- **Voitures** (`gen_cars.py`) : la carrosserie est un *loft* de sections à 12 points le long de
  X ; chaque type est un dictionnaire de profils (`belt` = ligne de caisse, `roof`, `clear` =
  garde au sol, `width`) indexés par x en mètres, plus les x des montants (`ws` pare-brise,
  `rf`/`rr` pavillon, `rw` lunette, `bpil` montant B). Les passages de roue sont creusés dans le
  profil bas. Vitres, montants et soubassement sont des bandes de matériaux du même maillage ;
  plis (crease) sur la ligne de caisse et les contours de vitres, subdivision 1 appliquée, lissage
  auto. Phares, feux, calandre, pare-chocs, rétros et poignées sont posés par lancer de rayon
  sur la carrosserie. Nouvelle voiture = nouvelle entrée dans `CARS`.
- **Humains** (`gen_human.py`) : corps sculpté en métaballes (ellipsoïdes/capsules, `build_elements`),
  chaque élément porte son os et sa zone de vêtement ; maillage dense → matériaux par zone
  (ourlets droits taille/manches, ligne des cheveux `scalp()`) → décimation → calotte de cheveux
  décalée + volumes de cheveux (femme) → yeux posés par rayon. Les poids de peau sont calculés
  avec le même champ implicite que la surface (articulations douces, pas de bone heat).
  Les animations sont des fonctions `t ∈ [0,1] → pose` (`idle_pose`, `walk_pose`, ...).
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
(caméra ajustée à la boîte englobante), éclairage studio 3 lumières + sol, 640×400, et écrit
`models/previews/<nom>.png`. Les humains sont posés à l'image 1 de `Idle`. Sans écran, Eevee
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
