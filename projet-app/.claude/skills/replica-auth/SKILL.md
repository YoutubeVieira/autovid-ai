---
name: replica-auth
description: "Câble l'authentification du clone (email + mot de passe, lien magique, Google) avec Supabase Auth, profils et protection des routes. Utiliser pour « login », « inscription », « auth », « replica-auth »."
---

# /replica-auth

1. Supabase Auth : email/mot de passe + lien magique ; Google OAuth si l'original le propose.
2. Table `profiles` (id = `auth.users.id`) créée par trigger à l'inscription ; RLS `id = auth.uid()`.
3. Middleware Next.js : routes `/app/*` protégées, redirection vers `/login?next=…`.
4. Écrans : connexion, inscription, mot de passe oublié, réinitialisation, déconnexion.
5. Onboarding : la première valeur en < 60 s (ex. créer son premier rendez-vous), comme le parcours n°1 de `recon.md`.
6. Teste : inscription → email → connexion → accès refusé aux données d'un autre compte.
