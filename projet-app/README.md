# Projet application — Replica

Inspiré de la vidéo 2 (voir [`../ANALYSE.md`](../ANALYSE.md)) : 11 skills Claude Code qui transforment « je veux une app comme X » en ton propre produit en ligne et payant.

> On reconstruit **ce que fait** une app (fonctionnalités, parcours), jamais **ce qu'elle possède** (code, marque, textes, images).

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
> /replica-recon Calendly
```
Enchaînement : `recon` → `reviews` → `plan` → `design` → `build` (+ `auth`, `pay`) → `test` → `diff` (boucle jusqu'à 100 % des *Must*) → `brand` → `launch`.

Tous les livrables intermédiaires sont écrits dans `replica/` (recon.md, reviews.md, plan.md, diff.md…), ce qui permet de reprendre le travail dans une nouvelle session.

Le contenu de lancement se fait avec le [projet vidéo](../projet-video/) : `/replica-launch` prépare le brief, `/yt-script` et `/yt-edit` produisent le Short.
