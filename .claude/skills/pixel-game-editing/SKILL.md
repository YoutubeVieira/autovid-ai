---
name: pixel-game-editing
description: Assemble un episode 3D en video finie style jeu (HUD, badges +1, sous-titres pixel, bruitages, voix, carton de fin, -14 LUFS) avec le preset pixel_game.
---
# pixel-game-editing
```bash
cd editor
python3 -m autoeditor run <frames/> --out-dir out/ --preset pixel_game \
   --events <frames/events.json> --audio <voix/voice.wav> --srt <voix/voice.srt> [--music musique.mp3]
```
Le preset `pixel_game` ne coupe pas les silences (le montage visuel est cale sur la voix), affiche le HUD (titre du jour + compteur N / 100), les badges (`yellow` +1 habitant, `green` emploi, `red` bloque), les sous-titres en police pixel (`packs/fonts`), un carton de fin de 2,2 s et les bruitages du pack CC0. Reglages dans `editor/presets/pixel_game.json` (titre, compteur max, tailles, tables de sons). Controle qualite automatique: 1080x1920, -14 LUFS, crete <= -1,5 dBTP.
