---
name: srt-translate
description: Traduit des sous-titres en conservant les horodatages (export JSON -> traduction -> reimport SRT), avec controle de longueur.
---
# srt-translate
```bash
cd editor
python3 -m autoeditor srt export video.srt --out cues.json --lang en     # 1) extrait les repliques
# 2) ajouter "translation" a chaque replique dans cues.json (sens + ton, court)
python3 -m autoeditor srt import cues.json --out video.en.srt           # 3) SRT traduit, memes temps
```
Les avertissements `trop long` indiquent les repliques > 135 % de l'original: les raccourcir. Pour la voix: reecrire le script minute dans la langue cible (une phrase par ligne, horodatee) puis `french-voices`/une voix de la langue (les voix libres du depot sont francaises; pour une autre langue, telecharger un modele Piper de cette langue).
