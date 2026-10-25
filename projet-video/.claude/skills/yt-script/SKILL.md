---
name: yt-script
description: Écrit le script complet d'une vidéo YouTube (longue ou Short) dans la voix du créateur, en partant d'une des 21 formules de hook. Utiliser pour « écris le script », « roteiro », « script de vidéo », « hook ».
---

# /yt-script — le script, dans ta voix

## Avant d'écrire
1. Lis `profil/voice.md` (tics de langage, tutoiement/vouvoiement, mots interdits, longueur de phrases). Annonce « lu : profil/voice.md ». S'il est vide, demande 3 transcriptions ou textes du créateur et remplis-le d'abord.
2. Ouvre `formules.md` et choisis **3 hooks** candidats adaptés au sujet. Montre-les numérotés `n / 21` et laisse l'utilisateur choisir (ou choisis le plus fort si on te dit d'avancer).

## Structure imposée
```
[HOOK]    0–3 s  : promesse ou choc. Une phrase. Pas de « salut ».
[PREUVE]  3–8 s  : pourquoi me croire (chiffre, démo, résultat).
[CORPS]          : 3 à 7 blocs ; chaque bloc = 1 idée + 1 visuel.
[VIRAGE]         : relance à mi-parcours (« mais le plus fou… »).
[CTA]            : une seule action (commenter un mot, lien, abonnement).
```
- Short : 90–130 mots, 35–50 s. Long : 1 300–1 600 mots pour 10 min.
- Une phrase = une ligne = un sous-titre. 4 à 9 mots par ligne.
- Marque les mots à surligner en rouge avec `*astérisques*` (1 par ligne max).
- Sous chaque bloc, indique `visuel:` (terminal, gros chiffre, grille, barres, classement, checklist, score, titre) — c'est ce que lit `/yt-edit`.

## Sortie
`scripts/<slug>.md` avec le script, puis propose `/yt-package` (titre + miniature) et `/yt-edit` (montage).
