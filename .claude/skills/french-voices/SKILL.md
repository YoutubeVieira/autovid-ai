---
name: french-voices
description: Genere une voix off francaise gratuite hors-ligne calee sur un script minute horodate (Piper). Donne voice.wav + voice.srt.
---
# french-voices
```bash
pip install piper-tts
python3 packs/voices/download_voices.py siwis            # modele ~70 Mo, telecharge a la demande
python3 packs/voices/tts.py script.txt --out voix/ --voice siwis --total 20
```
Script: `<debut_s> | <phrase>` par ligne (voir `blender/blocky/episode01/script_fr.txt`). Sortie: `voix/voice.wav` (piste calee), `voice.srt` (sous-titres exacts), `voice.json` (credit, avertissements de debordement).
Licences (lues dans les fiches des modeles): `siwis` CC BY 4.0 (commercial OK avec mention: "Voix: SIWIS, University of Edinburgh, CC BY 4.0"); `tom` AGPLv3 et `upmc` CC BY-SA 4.0: a verifier avant monetisation. Reglage `--speed 1.1` pour un rythme plus vif. Voix neuronale gratuite = correcte mais pas expressive: pour de l'emotion, utiliser un comedien ou un service de voix sous licence commerciale.
