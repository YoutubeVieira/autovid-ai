---
trigger: always_on
---

# Projet application

Suis `CLAUDE.md` à la racine de ce dossier : il dit quel agent prend quelle demande et donne les règles du projet.

- Les agents sont des fichiers `.claude/agents/<nom>.md` : quand une demande correspond à un agent, lis ce fichier et suis ses instructions.
- Les skills (`.claude/skills/<nom>/SKILL.md`) se lisent de la même façon quand un agent les cite.
- Workflows disponibles : voir `.agent/workflows/`.
- Jamais : publier, programmer, dépenser (génération payante) ou mettre en production sans l'accord explicite de l'utilisateur ; coller une clé dans la conversation ; committer les fichiers de l'utilisateur.
