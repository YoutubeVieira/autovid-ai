---
name: monde-peuple
description: Peuple le monde de la série: registre des habitants, parsing des commentaires (prénom + métier), plan d'épisode de 25-30 s, apparence par métier, expressions de visage.
---
# monde-peuple
`python3 monde/monde.py ajouter --episode N --titre "..." --commentaires f.txt [--max 30] [--simuler]` ; `python3 monde/monde.py etat`.
Entrées acceptées: `Léa, boulangère` / `Karim - pompier` / `Moi c'est Zoé, je veux être astronaute`. Métiers → apparence dans `monde/metiers.json` (alias sans accent; ajouter ses propres métiers). Le plan met en avant jusqu'à 5 habitants (un par métier d'abord), les autres arrivent en foule (« Et N autres encore »). Paliers: 15 = conseillers, 100 = élection du maire.
Rendu: `blender/blocky/episode_monde.py` (habitants anciens déjà présents, nouveaux qui arrivent, prénom + métier au-dessus de la tête, expression de visage parmi 12: `blocky.EXPRESSIONS`, changeable image par image avec `set_face`).
Règles: prénom seulement, pas de lien/contact/insulte, pas de genre deviné, pas d'habitants inventés présentés comme réels.
