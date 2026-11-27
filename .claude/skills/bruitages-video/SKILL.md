---
name: bruitages-video
description: Générer des bruitages originaux (sans droits) et les placer automatiquement au bon moment dans les vidéos Néon Studio (whoosh sur les coupes, impacts sur les flashs et accroches, montées avant les cartes noires, sirène, moteurs, pluie, grondement de fusée, signature finale). À utiliser pour toute vidéo qui « sonne plat », avant de publier sur TikTok ou YouTube.
---

# Bruitages générés et sound design automatique

## 1. Placement automatique (toujours actif)
`tools/studio/render.js` lit le montage du projet et place les bruitages tout seul (`autoSfx`). Il suffit de lancer un rendu avec musique :

```bash
node tools/studio/render.js projet.json --res 720 --music usa --blur 3
```

| Ce que le rendu repère | Bruitage placé |
|---|---|
| coupes de caméra | whoosh, alterné gauche/droite |
| flashs | impact |
| ralentis | montée, impact, puis grondement |
| accroche du début | impact |
| textes | pop |
| cartes noires | montée |
| dernière carte | signature |
| police dans la scène | sirène |
| véhicules qui roulent | moteurs |
| pluie | pluie |
| fusée | grondement |

`--sfx 0` désactive le placement automatique.

## 2. Bruitages en fichiers (meilleure qualité, sons choisis)
```bash
node tools/sound/bruitages.js tout --out marketing/sons --variantes 3   # génère <type>.wav (+ variantes)
node tools/studio/render.js projet.json --music usa --sons marketing/sons
```
Avec `--sons`, chaque type pour lequel `<dossier>/<type>.wav` existe utilise ce fichier au lieu de la synthèse. Les sons longs (sirène, pluie, moteur, grondement) sont bouclés et coupés à la bonne durée. Le mixage est limité pour ne jamais saturer, puis normalisé à −14 LUFS.

Les fichiers peuvent venir de `bruitages.js` (sons générés), ou d'Openverse choisis par l'oreille : skills `sons-openverse` puis `ecoute-sons`.

## Types disponibles
`whoosh`, `impact`, `riser`, `siren`, `engine`, `rumble`, `rain`, `pop`, `sting`. Ils sont synthétisés dans `js/audio.js` (`sfxWhoosh`, `sfxImpact`…), sans fichier externe.
