---
name: replica-test
description: Teste le clone à la recherche d'erreurs — tests end-to-end des parcours clés avec Playwright, cas limites, sécurité RLS — et corrige ce qui casse. Utiliser pour « teste l'app », « trouve les bugs », « QA », « replica-test ».
---

# /replica-test — chasser les erreurs

1. **Parcours** : un test Playwright par parcours de `recon.md` (`tests/e2e/<parcours>.spec.ts`).
2. **Cas limites** à toujours tester : champs vides / trop longs, double clic sur « payer », fuseaux horaires (créer à Paris, lire à São Paulo), mobile 390 px, connexion lente, session expirée.
3. **Sécurité** : avec deux comptes A et B, vérifier que B ne lit ni ne modifie les données de A (API et UI).
4. **Accessibilité** : navigation clavier sur les parcours, labels des champs.
5. Lance `npx playwright test` ; pour chaque échec : cause racine → correctif → relance. Ne désactive jamais un test pour passer au vert.

Sortie : `replica/test-report.md` (parcours ✓/✕, bugs trouvés et corrigés, ce qui reste).
