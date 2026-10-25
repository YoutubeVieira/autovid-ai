---
name: replica-build
description: Construit le clone jalon par jalon à partir du plan — écrans, logique, base de données — et le garde toujours lançable. Utiliser pour « construis l'app », « code le clone », « replica-build ».
---

# /replica-build — reconstruire

Pré-requis : `replica/recon.md`, `replica/plan.md` validés. Sinon, lance d'abord `/replica-recon` et `/replica-plan`.

## Boucle par jalon
1. Annonce le jalon et les écrans (`E02`, `E05`…) concernés.
2. Code : routes, composants, requêtes Supabase typées, validations (zod), états vides / chargement / erreur.
3. Lance l'app (`npm run dev`) et le typecheck/lint ; corrige avant de continuer.
4. Mets à jour la checklist dans `replica/progress.md` : `[x] E02 Agenda — créer / déplacer / annuler un RDV`.
5. Commit : `feat(J2): agenda — création et déplacement de rendez-vous`.

## Règles
- Jamais de secret dans le code : `.env.local` + `.env.example`.
- Les données d'exemple sont inventées (pas de vrais utilisateurs de l'original).
- Un jalon n'est fini que quand `/replica-test` passe dessus.
