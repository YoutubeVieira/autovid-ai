---
trigger: always_on
---

# AutoVid AI — 3 projets

Ce dépôt contient 3 projets indépendants : `projet-video/` (Shorts, 7 styles, machine à Reels, analyses), `projet-senior-us/` (gym douce pour seniors américains) et `projet-app/` (applications web et mobiles).

- Avant d'agir dans un projet, lis son `CLAUDE.md` (et `AGENTS.md` s'il existe) : il dit quel agent suit quelle demande.
- Les agents sont des fichiers `.claude/agents/<nom>.md` : quand une demande correspond à un agent, lis ce fichier et suis ses instructions, comme le ferait Claude Code.
- Les workflows `/video-…`, `/senior-…`, `/app-…` couvrent les demandes courantes.
- Réponds en français ; le contenu destiné au public suit la langue du projet (anglais américain pour `projet-senior-us`).
- Jamais : publier, programmer, dépenser (génération payante) ou mettre en production sans l'accord explicite de l'utilisateur ; coller une clé dans la conversation ; committer les médias de l'utilisateur (`entrees/`), les analyses (`analyses/`) ou les outils tiers (`externes/`).
