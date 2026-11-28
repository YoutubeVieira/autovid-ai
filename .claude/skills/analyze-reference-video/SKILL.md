---
name: analyze-reference-video
description: Analyse une video de reference (format, rythme de coupe, silences, loudness, structure hook/corps/CTA) pour en extraire un style reproductible. A utiliser quand l'utilisateur donne une video "modele".
---
# analyze-reference-video

```bash
cd editor && python3 -m autoeditor analyze <video.mp4> --out analysis.json
```
Donne: duree, resolution, fps, silences, changements de plan, loudness integree. Completer par:
- planche de vignettes: `ffmpeg -i v.mp4 -vf "fps=1/2,scale=216:-1,tile=6x3" -frames:v 1 planche.png`, puis la regarder;
- coupes plus fines: `-vf "select='gt(scene,0.08)',showinfo"` (le seuil 0,25 rate les coupes douces).
Rediger: structure avec horodatages, rythme (plans par 10 s), sous-titres, son. Transformer les constats en reglages de preset (voir `docs/ANALYSE.md`). Si le fichier est protege par des droits, extraire des regles de style, jamais du contenu a reutiliser.
