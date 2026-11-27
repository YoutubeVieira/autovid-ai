# autoeditor - monteur video autonome

Pipeline ffmpeg + Python standard (aucune dependance pip) pour transformer un rush en video courte verticale.

```bash
cd editor
python3 -m autoeditor analyze rush.mp4                       # silences, plans, loudness
python3 -m autoeditor run rush.mp4 --out-dir out \
    --srt rush.srt --hook "Texte d'accroche" --music musique.mp3
python3 -m unittest discover -s tests -v                     # tests de bout en bout
```

Sorties dans `out/` : `analysis.json`, `plan.json` (EDL), `captions.ass`, `final.mp4`, `qa.json`.
Le style se regle dans `presets/shortform_9x16.json` (derive de `docs/ANALYSE.md`).
Sans `--srt`, la transcription automatique est utilisee si `faster-whisper` ou `whisper` est installe, sinon la video est montee sans sous-titres.
Code de retour 0 si le controle qualite passe, 1 sinon.

## Style "jeu de ville" (preset `pixel_game`)
```bash
python3 -m autoeditor run <dossier_images/> --out-dir out --preset pixel_game \
    --events <dossier_images>/events.json --audio voix/voice.wav --srt voix/voice.srt
python3 -m autoeditor srt export video.srt --out cues.json --lang en     # traduction de sous-titres
```
HUD (titre + compteur), badges +1, sous-titres pixel, bruitages (`../packs/sfx`), carton de fin, voix off, loudness -14 LUFS.
