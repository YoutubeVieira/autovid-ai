---
name: blocky-episode
description: Construit, anime et rend un episode 3D de la ville peuplee dans Blender (bpy), avec evenements pour le monteur autonome.
---
# blocky-episode
Modele: `blender/blocky/episode01.py` (20 s, 24 i/s, 5 plans). Lancer:
```bash
pip install bpy
python episode01.py -- --out frames/ --res 450 800 --samples 12 --blend episode01.blend   # ~4 s/image sur 4 coeurs
python episode01.py -- --out frames/ --range 130 130 --res 405 720 --samples 12            # une image de test
```
Sorties: `frames/f_0001.png...`, `frames/events.json` (compteur, badges, coupes, palier), `episode01.blend` (projet ouvrable). Camera: un objet par plan + marqueur lie (`shot(i, loc0, loc1, tgt0, tgt1, lens)`). Look jouet: `Khronos PBR Neutral`, exposition -0,6, ciel a diffusion multiple; les sRGB sont convertis dans `mat()`.
Assemblage: voir la skill `pixel-game-editing`.
