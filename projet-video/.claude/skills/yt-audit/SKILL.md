---
name: yt-audit
description: Audite une chaîne YouTube complète — packaging, régularité, rétention, formats, conversions — et rend un plan d'action classé. Utiliser pour « audit de ma chaîne », « pourquoi ma chaîne ne grandit pas », « analyse ma chaîne ».
---

# /yt-audit — l'état de la chaîne

## Données
Demande (ou lis dans `audit/`) : l'export YouTube Studio des 90 derniers jours (vidéos, vues, CTR des impressions, durée moyenne, abonnés gagnés) et l'URL de la chaîne. Sans export, travaille sur les titres et vues publics et précise la limite.

## Contrôles
| Axe | Question | Seuil |
|-----|----------|-------|
| Packaging | CTR moyen des impressions | < 4 % = problème de titre/miniature → `/yt-package` |
| Hook | rétention à 30 s | < 60 % (long) / < 75 % (Short) → `/yt-script` |
| Rétention | durée moyenne / durée | < 35 % → `/yt-retention` |
| Régularité | écart entre publications | > 10 jours ou irrégulier → `/yt-plan` |
| Formats | part de Shorts vs longs, et qui amène les abonnés | |
| Outliers | quelles vidéos font ≥ 3× la moyenne et pourquoi | → `/yt-viral` sur ses propres vidéos |
| Conversion | abonnés gagnés pour 1 000 vues | |

## Sortie
`audit/audit-AAAA-MM-JJ.md` : note par axe (A–E), les 5 actions classées par impact, et la skill à lancer pour chacune.
