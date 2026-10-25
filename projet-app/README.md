# Projet application — Replica

Inspiré de la vidéo 2 (voir [`../ANALYSE.md`](../ANALYSE.md)) : 11 skills Claude Code qui transforment « je veux une app comme X » en ton propre produit en ligne et payant.

> On reconstruit **ce que fait** une app (fonctionnalités, parcours), jamais **ce qu'elle possède** (code, marque, textes, images).

## Les 7 agents

| Agent | Rôle |
|-------|------|
| `chercheur-produit` | analyse l'app de référence et ses avis |
| `architecte-app` | web, mobile ou les deux ; stack, schéma Supabase, jalons |
| `designer-ui` | design system partagé web + mobile, maquettes, logo |
| `dev-web` | application web Next.js + Supabase, responsive et installable (PWA) |
| `dev-mobile` | application mobile iOS/Android avec Expo (React Native) |
| `testeur-qa` | tests e2e, sécurité, accessibilité, couverture vs l'original |
| `lanceur` | marque, landing, déploiement, fiche store, vidéo de lancement |

Web + mobile ensemble = monorepo `apps/web`, `apps/mobile`, `packages/shared` sur une seule base Supabase (décidé par `architecte-app`). L'ordre et les règles communes sont dans [`CLAUDE.md`](CLAUDE.md).

## Les 11 skills

| Étape | Commande | Rôle |
|-------|----------|------|
| Comprendre | `/replica-recon` | démonte l'app : écrans, parcours, fonctionnalités, modèle de données, prix |
| | `/replica-reviews` | « l'entrepreneur » : lit 100+ avis et trouve les problèmes à résoudre |
| Concevoir | `/replica-plan` | stack, schéma SQL avec RLS, jalons |
| | `/replica-design` | design system propre au clone |
| Construire | `/replica-build` | code jalon par jalon, toujours lançable |
| | `/replica-auth` | connexion, inscription, routes protégées |
| | `/replica-pay` | abonnements Stripe / PIX, webhooks |
| Vérifier | `/replica-test` | tests Playwright, cas limites, sécurité |
| | `/replica-diff` | ce qui manque encore par rapport à l'original |
| Vendre | `/replica-brand` | nom, promesse, logo, landing page |
| | `/replica-launch` | déploiement, mentions légales, fiche store, contenu de lancement |

## Démarrer
```bash
mkdir mon-app && cp -r projet-app/.claude mon-app/ && cd mon-app
claude
> Je veux une app comme Calendly, en web et en mobile.
```
Claude enchaîne les agents ; chaque agent suit les skills ci-dessus. Enchaînement des skills : `recon` → `reviews` → `plan` → `design` → `build` (+ `auth`, `pay`) → `test` → `diff` (boucle jusqu'à 100 % des *Must*) → `brand` → `launch`.

Tous les livrables intermédiaires sont écrits dans `replica/` (recon.md, reviews.md, plan.md, diff.md…), ce qui permet de reprendre le travail dans une nouvelle session.

Le contenu de lancement se fait avec le [projet vidéo](../projet-video/) : l'agent `lanceur` prépare le brief, les agents `scenariste` et `monteur-video` produisent le Short.
