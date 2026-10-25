# Projet application — Replica

Concevoir, construire et lancer des applications **web** et **mobiles** à partir d'une app existante, en résolvant ce que ses utilisateurs détestent.

## Quel agent pour quoi
| Besoin | Agent |
|--------|-------|
| analyser l'app de référence, lire les avis | `chercheur-produit` |
| stack, web vs mobile, base de données, jalons | `architecte-app` |
| design system, maquettes, logo | `designer-ui` |
| application web (Next.js, PWA) | `dev-web` |
| application mobile iOS/Android (Expo) | `dev-mobile` |
| tests, bugs, ce qui manque | `testeur-qa` |
| marque, landing, déploiement, stores | `lanceur` |

## Ordre
`chercheur-produit` → `architecte-app` (validation de l'utilisateur) → `designer-ui` → `dev-web` et/ou `dev-mobile` (en parallèle si monorepo, après le schéma) → `testeur-qa` (boucle avec les devs jusqu'à 100 % des *Must*) → `lanceur`.

Mémoire partagée : le dossier `replica/` (`recon.md`, `reviews.md`, `plan.md`, `progress.md`, `test-report.md`, `diff.md`). Chaque agent lit l'état avant d'agir et le met à jour après.

## Règles
- Reconstruire ce que l'app **fait**, jamais ce qu'elle **possède** (code, marque, textes, images).
- Aucun secret dans le code ; RLS sur chaque table.
- Pas de déploiement en production, de soumission aux stores ni de paiement réel sans accord explicite de l'utilisateur.
