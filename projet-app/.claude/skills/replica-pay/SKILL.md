---
name: replica-pay
description: Met en place les abonnements et paiements du clone (Stripe, PIX via PSP local), la page de prix et les webhooks qui activent le plan. Utiliser pour « paiement », « abonnement », « Stripe », « PIX », « replica-pay ».
---

# /replica-pay — encaisser

1. **Prix** : depuis `recon.md`, propose une grille plus simple que l'original (souvent un plan unique à prix fixe, si « le prix augmente » ressort dans `reviews.md`).
2. **Stripe** : produits/prix créés par script (`scripts/stripe-seed.ts`), Checkout en mode `subscription`, portail client pour gérer/annuler.
3. **PIX** (cible Brésil) : via un PSP qui gère PIX (Stripe BR, Mercado Pago, ou autre choisi par l'utilisateur) ; QR code + confirmation par webhook.
4. **Webhooks** `/api/webhooks/<psp>` : vérification de signature, idempotence (table `payments` avec `event_id` unique), mise à jour de `subscriptions.status`.
5. **Garde-fou** : les fonctionnalités payantes vérifient le statut côté serveur, jamais seulement côté client.
6. Teste en mode test : paiement réussi → « PAGO / payé », échec, annulation, renouvellement.

Clés uniquement dans `.env.local` ; documente les variables dans `.env.example`.
