---
description: "Construire sa propre application à partir d'une app existante (méthode Replica), web et/ou mobile"
---

1. Lis `CLAUDE.md` : ordre des agents et règles (reconstruire ce que l'app fait, jamais ce qu'elle possède).
2. Analyse : suis `.claude/agents/chercheur-produit.md` (skills `replica-recon`, `replica-reviews`).
3. Plan : suis `.claude/agents/architecte-app.md` et fais valider le plan par l'utilisateur.
4. Design et code : `designer-ui`, puis `dev-web` et/ou `dev-mobile` (fichiers `.claude/agents/*.md`), jalon par jalon.
5. Tests : `.claude/agents/testeur-qa.md` jusqu'à 100 % des fonctions indispensables ; lancement : `.claude/agents/lanceur.md` (jamais de mise en production sans accord).
