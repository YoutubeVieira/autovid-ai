---
name: caption-style
description: Cree et regle les sous-titres dynamiques (1 a 3 mots, mot cle en couleur) et le bandeau d'accroche.
---
# caption-style

Les sous-titres sont generes en ASS depuis un SRT (`autoeditor/captions.py`) puis incrustes; les temps sont recalcules sur la timeline apres coupes.
Reglages `captions` du preset: `font`, `size` (84 sur 1080 px de large), `max_words` (3), `uppercase`, `primary`, `highlight` (mot cle, jaune), `outline`, `margin_v` (zone basse). Bandeau d'accroche: `hook` + option `--hook "texte"` (6 mots max, retour a la ligne automatique tous les ~22 caracteres).
Le mot en surbrillance est le plus long du groupe (>= 5 lettres): pour le choisir a la main, editer `captions.ass` apres generation. Police par defaut: DejaVu Sans (installee partout); en installer une autre et changer `font` pour un autre look.
