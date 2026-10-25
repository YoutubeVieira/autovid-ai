---
name: replica-plan
description: Choisit la stack, conçoit la base de données et découpe la construction du clone en étapes livrables. Utiliser après /replica-recon, pour « plan technique », « quelle stack », « schéma de base », « replica-plan ».
---

# /replica-plan — stack, base, étapes

## Stack par défaut (à changer seulement avec une raison)
| Besoin | Choix |
|--------|-------|
| Web + mobile web | Next.js (App Router) + TypeScript + Tailwind + shadcn/ui |
| Base + auth + stockage | Supabase (Postgres, RLS) |
| Paiement | Stripe (carte) ; PIX via un PSP brésilien si la cible est au Brésil |
| Emails / SMS | Resend / Twilio |
| Déploiement | Vercel |
| Mobile natif (si l'original est une app native) | Expo (React Native) |

## Livrables
1. `replica/plan.md` : stack retenue + justification d'une ligne par choix.
2. `supabase/migrations/0001_init.sql` : tables issues du modèle de `recon.md`, clés étrangères, index, **politiques RLS sur chaque table** (un utilisateur ne voit que ses lignes).
3. Découpage en **jalons**, chacun démontrable :
   - J1 squelette + auth · J2 action principale (le *Must* n°1) · J3 autres *Must* · J4 paiement · J5 réponses aux problèmes de `reviews.md` · J6 landing + lancement.

Demande validation du plan avant `/replica-build`.
