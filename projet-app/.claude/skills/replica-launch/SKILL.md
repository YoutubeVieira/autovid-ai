---
name: replica-launch
description: Met le clone en ligne et le prépare à vendre — déploiement, domaine, fiche App Store / Google Play, mentions légales, analytics, premier contenu de lancement. Utiliser pour « déployer », « mettre en ligne », « fiche store », « lancement », « replica-launch ».
---

# /replica-launch — mettre en vente

## Checklist (bloquante)
- [ ] `/replica-test` vert, `/replica-diff` à 100 % des *Must*
- [ ] Variables de prod configurées (Supabase, Stripe live, emails)
- [ ] Déploiement Vercel + domaine + HTTPS
- [ ] Mentions légales, CGV, politique de confidentialité (RGPD / LGPD selon la cible) — modèles à faire relire
- [ ] Analytics (Plausible ou PostHog) + suivi de conversion du paiement
- [ ] Monitoring d'erreurs (Sentry)

## Fiche store (si app mobile)
Titre (30 car.), sous-titre, description, mots-clés, 5 captures annotées, catégorie — écrits autour de la promesse de `/replica-brand`.

## Contenu de lancement
Script d'un Short de 40 s au format du `projet-video` (hook « Avant / Après » avec les problèmes résolus) → à passer à `/yt-script` puis `/yt-edit`.
