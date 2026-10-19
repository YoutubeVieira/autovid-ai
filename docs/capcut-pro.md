# CapCut Pro → AutoVid : ce que fait l'automate

Inventaire des fonctions de montage et d'animation de CapCut (mobile, PC et Pro) et leur équivalent automatique
dans AutoVid. « Auto » = fait sans intervention ; « Plateforme » = réglable dans Studio Jacobina.

| CapCut | AutoVid | Où |
|---|---|---|
| Courbe de vitesse : Montage, Héros, Bullet, Jump cut, Flash in, Flash out | Préréglages `heros`, `bullet`, `montage`, `flash_in`, `flash_out`, `constant` autour de chaque coup | `effets.py`, `--courbe`, Plateforme |
| Ralenti fluide (optical flow) | Fondu entre images voisines (pas d'interpolation de mouvement) | `combat.Renderer.render` |
| Images clés (zoom, position) | Zoom qui suit le membre qui travaille, tremblement à l'impact | `fluide.py` (auto) |
| Transitions (zoom, whip, glitch, flash) | `zoom`, `whip`, `glitch`, `flash`, `mix` à chaque coupe | `effets.py`, `--transition`, Plateforme |
| Effets (shake, flash, RGB split, étoile d'impact) | Tremblement, flash RVB, étoile d'impact, grain, vignette | `fluide.py` (auto) |
| Filtres / étalonnage | `cine` (teal & orange), `vif`, `chaud`, `froid`, `nb` + étalonnage contraste automatique | `effets.FILTRES`, `--filtre`, Plateforme |
| Sous-titres automatiques animés | Mot prononcé en jaune avec un pop, 3 mots max, SRT FR / PT-BR / EN | `talk.captions_ass` (auto) |
| Modèles de texte | Titres en 2 lignes (blanc + jaune), accroche, ligne ATTENTION, muscles | `fluide.py`, Plateforme |
| Texte → voix (TTS) | Kokoro (local) ou ta voix clonée ElevenLabs, mots capoeira en portugais | `narration.py` |
| Réduction du bruit | Passe-haut + `afftdn` sur le son d'origine | `combat.py`, Plateforme |
| Ducking automatique | La musique et le son d'origine baissent sous la voix | `combat.build_audio` (auto) |
| Synchro sur le beat | Un temps fort de la musique tombe pile sur le premier impact | `effets.beat_offset` (auto) |
| Bibliothèque de sons | Bruits synthétisés selon le contact : corps, sac / pao, vide, rotation | `sfx.py` (auto) |
| Recadrage auto (9:16, 16:9) | 9:16 cover / flou pour les shorts, 16:9 pour la vidéo longue | `normalize`, `long.py` |
| Suppression des silences | Coupe des blancs, « euh » et reprises | `talk.py` |
| Long → courts (AI clips) | Un short par mouvement à partir de la même vidéo | `viral.py` |
| Écran partagé | Short 9:16 + fiche dans la vidéo longue | `long.py` |
| Retouche visage, chroma key, suppression de fond | Pas fait (inutile pour l'analyse de mouvement) | — |
| Stabilisation | Pas fait (à ajouter avec `vidstab` si les rushs tremblent) | — |
| Modèles de projet complets | Projet `projet.json` modifiable dans la plateforme | `projet.py`, Plateforme |

## L'automate `viral`

```
python -m autovid viral roda.mp4 -o projet_roda/ --discipline capoeira --handle @capoeirajacobina
```

Une vidéo donne :

1. **Short principal** (toutes les analyses, 9:16, ~30 s).
2. **Vidéo longue YouTube 16:9 à chapitres**, construite pour la rétention :
   - Intro : l'accroche, puis « au programme » (le plan annoncé tout de suite).
   - Pour chaque mouvement : carte titre, le mouvement en vrai à vitesse normale, puis l'analyse au ralenti avec sa fiche (placement, muscles, risque, astuce).
   - Le meilleur moment est placé vers les 2/3 de la vidéo et annoncé dès l'intro (« le plus important : chapitre X »).
   - Fin : abonnement et prochaine vidéo.
   - Les chapitres YouTube sont écrits dans `longue_youtube.chapitres.txt`.
3. **Un short par mouvement différent**, chacun avec sa propre accroche.
4. **`a_publier.md`** : titres, description avec chapitres, hashtags, ordre de publication. La vidéo longue sort d'abord, puis un short par jour qui renvoie vers elle.

Plus la vidéo d'origine est longue (cours complet, roda de 10 min), plus la vidéo longue a de chapitres (`--max-impacts`).

Sources consultées : page officielle CapCut sur les courbes de vitesse, guides tiers sur les préréglages et l'auto
reframe, articles sur la rétention YouTube (chapitres, boucles ouvertes, meilleur moment aux 2/3).
