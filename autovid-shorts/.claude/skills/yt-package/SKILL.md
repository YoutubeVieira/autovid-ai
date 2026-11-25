---
name: yt-package
description: "Écrit et note le « package » d'une vidéo — titre + concept de miniature — sur 100 points, puis propose des versions améliorées. Utiliser pour « titre », « miniature », « thumbnail », « packaging », « CTR »."
---

# /yt-package — titre + miniature, notés sur 100

Titre et miniature se vendent **ensemble** : la miniature ne répète jamais le titre, elle le complète.

## Grille (100 pts)
| Critère | Pts | Règle |
|---------|-----|-------|
| Longueur | 15 | ≤ 60 caractères (coupé sur desktop au-delà) ; idéal 40–55 |
| Chiffre ou élément concret | 15 | un nombre, un nom, un prix, une durée |
| Écart de curiosité | 20 | on comprend le sujet, pas la réponse |
| Complémentarité miniature | 20 | la miniature ajoute une info ; 0 si elle répète le titre |
| Lisibilité miniature | 10 | ≤ 4 mots, 1 visage ou 1 objet, contraste fort |
| Promesse tenue | 10 | le script délivre vraiment ce que le titre promet |
| Mot-clé | 10 | le terme recherché est dans les 3 premiers mots (voir `/yt-seo`) |

## Sortie
Pour le package actuel :
```
"<titre>"
<n> caractères                         <score>/100
✕ <problème 1>
✕ <problème 2>
ok <ce qui marche>
```
Puis 5 variantes de titre (chacune notée) et 3 concepts de miniature (décor, sujet, texte ≤ 4 mots, couleur dominante). Recommande le meilleur couple.
