---
name: video-pixel-ville
description: Fabrique une vidéo verticale 720x1280 style "ville pixel" (carte vue de dessus, HUD, badges, sous-titres pixel) entièrement par code, dans la langue voulue.
---
# video-pixel-ville
1. Script minute dans la langue cible + voix: skill `voix-supertonic` (ou `french-voices`) -> `voice.json`, `voice.wav`, `voice.srt`.
2. Scènes: `python3 pixel/caragua_fr.py --voice <dossier voix> --out <dossier>` -> `source.mp4` (sans son ni texte) + `events.json`. Les plans suivent les phrases (indices de `cues`), les panneaux (POSTE, FERMÉE, 15, 0 / 100) sont dessinés dans la scène.
3. Assemblage: `python3 -m autoeditor run source.mp4 --out-dir out --preset pixel_game_720 --events events.json --audio voice.wav --srt voice.srt`.
Pour une autre langue: traduire `script_fr.txt` (skill `srt-translate`), régénérer la voix, relancer 2 et 3; les libellés dessinés sont dans `caragua_fr.py` et le preset.
