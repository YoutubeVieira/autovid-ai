---
name: analyser-video-reference
description: Analyser une vidéo de référence (mp4) avant de la refaire en code : type (motion design, archives, IA, talking head), format, rythme, effets, structure du récit, son. À utiliser quand l'utilisateur fournit un fichier vidéo ou demande « de quel type est cette vidéo », « refais-la », « même style ».
---

# Analyser une vidéo de référence

**Toujours analyser avant de produire.** Ne jamais deviner le type à partir du titre.

## Étapes
1. `cd video-engine && node tools/analyze-video.mjs <fichier.mp4>` → `info.json` (durée, format, fps, coupes, volume) et `planche.png`.
2. **Regarder** la planche avec Read (et 2-3 images plein format : `ffmpeg -ss <t> -i <mp4> -frames:v 1 f.png`). L'outil mesure ; le style se juge à l'œil.
3. Remplir la fiche ci-dessous et la sauvegarder dans `video-engine/veille/analyses/<nom>.md`.

## Fiche d'analyse
- **Type** : motion design 2D sur carte / archives vidéo / vidéo générée par IA / captation / mixte. Preuves : coupes détectées (peu de coupes + fond fixe = motion design), grain d'image, présence de plans filmés.
- **Format** : 9:16 ou 16:9, durée, fps.
- **Fond** : carte satellite, plan, fond uni…
- **Éléments animés** : pictogrammes, portraits, bulles, flèches, compteurs, drapeaux, remplissages de pays.
- **Caméra** : zooms, rebonds, travellings, secousses.
- **Sous-titres** : police, couleur, découpage (nombre de mots), position.
- **Voix** : langue, ton, débit ; musique/ambiances ; bruitages (whoosh, impacts).
- **Récit** : accroche (secondes 0-3), enchaînement des scènes, relances, chute, appel final. Noter un timing par scène.
- **Ce que le moteur sait déjà faire** (`video-engine/README.md`) et **ce qui manque** (liste des écarts).

## Si l'on refait la vidéo
Dresser la correspondance élément → champ du JSON de scène (`fills`, `items`: icon/flagBadge/person/bubble/tag/title/ping/arrow/burst/stat, `move`, `impacts`). Ne pas copier les visuels, textes ni portraits du fichier source : refaire = même mécanique, contenu original et droits propres.
Puis skill `short-carte-finance` pour écrire la nouvelle version.
