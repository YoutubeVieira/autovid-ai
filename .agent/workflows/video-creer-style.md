---
description: "Créer une vidéo dans un des 7 styles (motion, claymation, explainer, chanté, pub, 3D, cartoon)"
---

Travaille dans le dossier `projet-video/` : toutes les commandes et chemins ci-dessous s'entendent depuis ce dossier.

1. Lis `styles/STYLES.md` et suis `.claude/agents/directeur-creatif.md`.
2. Vérifie que l'outil du style est installé (`.claude/skills/<style>`, `externes/`) ; sinon demande à l'utilisateur de lancer `outils/installer-styles.ps1`.
3. Pour un style payant : estime le coût et attends l'accord explicite de l'utilisateur avant toute génération. Ne lis jamais une clé à voix haute ; elles sont dans `.env`.
4. Produis, vérifie avec `ffprobe`, livre le fichier et le coût réel.
