---
description: "Programmer et publier les vidéos approuvées sur Instagram, TikTok et YouTube"
---

1. Suis `.claude/agents/publicateur.md`.
2. `python outils/machine.py programmer`, puis lis `machine/semaines/<semaine>/publications.csv`.
3. Ne publie ou ne programme rien sans confirmation de l'utilisateur dans la conversation ; sinon prépare la liste pour la programmation native (YouTube Studio, Meta Business Suite, TikTok Studio).
4. Après chaque publication : `python outils/machine.py publie vN --plateforme <p> --url <lien>`.
