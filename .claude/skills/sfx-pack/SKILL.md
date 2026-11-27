---
name: sfx-pack
description: Pack de bruitages CC0 synthetises (ding, coin, pop, whoosh, level_up, stamp...) et leur placement automatique par evenements.
---
# sfx-pack
Dossier `packs/sfx/` (14 sons WAV, CC0, generes par `make_sfx.py`, aucune attribution). `manifest.json` decrit chaque son et son usage.
Placement automatique: `autoeditor run ... --events events.json --sfx-dir packs/sfx` joue le son associe a chaque evenement selon `sfx.map` du preset (`badge:yellow`->ding, `badge:green`->coin, `counter`->tick, `cut`->whoosh, `milestone`->level_up, carton de fin->stamp). Modifier la table dans le preset pour changer l'habillage. Regenerer/ajouter un son: editer `make_sfx.py` puis `python3 packs/sfx/make_sfx.py`.
Musique: aucune piste fournie (la synthese ne donne pas de bonne musique). Utiliser une musique dont on possede les droits avec `--music` (ducking automatique).
