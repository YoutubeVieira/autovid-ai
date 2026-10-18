---
name: montage-combat
description: Monte automatiquement une vidéo de sport de combat en short vertical éducatif et viral (ralentis, flash, arrêts sur image, zoom, membres colorés, cercles sur les articulations, angles, étiquettes d'anatomie, bruitages, musique, CTA). À utiliser dès que l'utilisateur donne une vidéo de combat, de boxe, de MMA, de muay thaï, de karaté, de capoeira ou de self-défense et veut un montage.
---

# Montage combat éducatif

## 1. Lancer le montage
```bash
python -m autovid combat "<video>" -o "sorties/<nom>_combat.mp4" --handle "<@compte>" \
    [--music musique.mp3] [--max-impacts 6] [--resolution 1080|4k] [--ai claude] --workdir "travail/<nom>"
```
- Pas de `--music` → beat généré (libre de droits, pas de Content ID).
- `--ai claude` si `ANTHROPIC_API_KEY` (ou `ant auth login`) est configuré : Claude regarde les images de chaque coup et rédige le titre, l'accroche, les muscles et l'astuce.
- Résolution : 1080 pour TikTok / Reels (ils recompressent en 1080p), 4k seulement pour un master YouTube. Ne propose pas la 8K pour publier : c'est un upscale, sans détail en plus.

## 2. Vérifier soi-même le résultat (obligatoire)
1. Lis `sorties/<nom>_combat.analyse.json` : liste des coups détectés (temps, nom, membre, muscles).
2. Fais une planche contact et **regarde-la** avec l'outil Read :
   ```bash
   ffmpeg -v error -y -i sorties/<nom>_combat.mp4 -vf "fps=1.5,scale=200:-1,tile=10x5" -frames:v 1 travail/<nom>/planche.jpg
   ```
3. Contrôle : chaque titre correspond-il au coup visible ? les couleurs sont-elles sur le bon membre ? un texte déborde-t-il ? le squelette est-il sur la bonne personne ?
4. Si un coup est mal nommé ou faux : relance avec `--ai claude`, ou baisse `--max-impacts`, ou découpe la vidéo d'entrée (`ffmpeg -ss … -to …`) autour de la bonne action.

## 3. Rendre compte
Donne le chemin du MP4, la liste des analyses, et ce qui reste imparfait. Propose ensuite le skill `feedback-montage`.

## Repères
- Lis `APPRENTISSAGES.md` dans ce dossier avant chaque montage : il contient les préférences de l'utilisateur.
- Les vidéos déjà montées (avec leurs propres titres) donnent un résultat chargé : préfère les rushs bruts.
