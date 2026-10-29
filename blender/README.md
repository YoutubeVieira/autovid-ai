# Projets Blender automatiques

`build_scene.py` cree un projet `.blend` complet a partir d'un OBJ: materiaux Principled (peau avec subsurface scattering, cheveux, tissus), eclairage studio 3 points, sol + fond en cyclo, camera avec profondeur de champ, rendu Cycles + denoise (AgX).

```bash
pip install bpy numpy          # Blender 5.0 comme module Python (Python 3.11), ~375 Mo
python build_scene.py --obj ../models/coach_senior_tpose.obj \
    --blend coach_scene.blend --render rendu_corps.png --samples 96 --res 1080 1080
python build_scene.py ... --close    # cadrage portrait
```
Avec Blender installe: `blender -b -P build_scene.py -- --obj ... --blend ...`.

Fichiers: `coach_scene.blend` / `coach_scene_portrait.blend` (projets ouvrables dans Blender), `rendu_corps.png` / `rendu_portrait.png`.

## Limite importante
Le projet est automatique et reproductible, mais le rendu est celui du **modele procedural** (formes simples, visage schematique): il n'atteint pas le rendu d'un film d'animation. Ce qui fait ce rendu (modelisation sculptee, textures peintes, cheveux en mèches, rig facial, eclairage et compositing d'un studio) n'est pas generable par script a partir de formes de base.
