---
name: blocky-characters
description: Cree des personnages-figurines articules en blocs colores pour Blender (corps, tete, bras a coude, jambes a genou, accessoires de metier), prets a animer.
---
# blocky-characters
Bibliotheque: `blender/blocky/blocky.py`. `make_character(name, collection, shirt=..., pants=..., hair="cap|spiky|bun|long|grey", hat="tophat|helmet|beret|cap|chef", accessory="sash|cross|whistle|apron|vest|bag", face="smile|happy|shock|angry")` retourne `(armature, maillage)`; 15 os (hanches, torse, tete, bras/avant-bras/main, cuisse/tibia/pied). Couleurs en sRGB (comme un nuancier). Poses/animations: `pose`, `walk`, `wave`, `cheer`, `idle`, `pop_in`, `key_obj`. Les os se tournent en X pour avancer/reculer et en Z pour lever un bras sur le cote (+/-150 degres).
Test visuel: `python gallery_test.py -- galerie.png` (necessite `pip install bpy`).
Personnages originaux: ne pas reproduire d'avatar ni de marque existante.
