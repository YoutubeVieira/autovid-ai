---
description: "Lancer ou faire avancer la machine à Reels : 7 vidéos, approbation, 1 publication par jour, analyse"
---

Travaille dans le dossier `autovid-shorts/` : toutes les commandes et chemins ci-dessous s'entendent depuis ce dossier.

1. Lis `machine/LISEZMOI.md` et suis `.claude/agents/chef-machine.md`.
2. `python outils/machine.py statut` pour savoir où en est la semaine (ou `semaine --debut <lundi>` pour en créer une).
3. Fais avancer chaque vidéo jusqu'à `a_approuver`, puis présente-les à l'utilisateur. N'appelle `machine.py approuver vN` que sur son accord explicite pour cette vidéo.
4. Termine par `machine.py statut` et ce que l'utilisateur doit faire maintenant.
