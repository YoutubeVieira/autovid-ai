---
name: copier-style
description: Copie le style de montage d'une vidéo de référence (YouTube, Reels, TikTok) — rythme des coupes, mise en page, titres, couleurs, effets — et l'applique aux rushs de l'utilisateur. À utiliser quand l'utilisateur montre un exemple de montage à reproduire.
---

# Copier un style de montage

1. Analyse chiffrée de la référence :
   ```bash
   python -m autovid analyze reference.mp4 -o analyse/
   ```
   → `analyse/<ref>/adn.json` (coupes, durée des plans, BPM, % de coupes sur le temps, loudness, mise en page) + `planche.jpg`.
2. **Regarde** `planche.jpg` (outil Read) et des images clés en grand :
   `ffmpeg -ss <t> -i reference.mp4 -frames:v 1 -vf scale=540:-1 analyse/img_<t>.jpg`
   Note : police (pinceau / condensée grasse), couleurs, position des textes (tiers haut ?), filigrane, transitions (cut, flash), zooms, ralentis, annotations (cercles, flèches, membres colorés), étalonnage.
3. Choisis le style le plus proche (`bincombat`, `stepbystep`) et écris un brief YAML (voir `examples/pull_counter.yaml`) : `beats`, `layout`, `transition`, `zoom`, `speed`, `markers`, `step`, `kicker/title`, `cta`, `watermark`, et `style_overrides` pour les couleurs / tailles / étalonnage.
4. `python -m autovid render brief.yaml -o sorties/copie.mp4`, puis compare les deux planches côte à côte et corrige le brief jusqu'à ce que ce soit proche.
5. Pour une vidéo de combat, `python -m autovid combat` donne déjà le style « analyse éducative » ; le brief sert pour les compilations.
