---
name: replica-design
description: "Reconstruit un design system propre au clone (couleurs, typo, espacements, composants) inspiré de l'ergonomie de l'original sans copier son identité. Utiliser pour « design system », « UI du clone », « replica-design »."
---

# /replica-design — un design à toi

On reprend l'**ergonomie** (où sont les choses, combien de clics) ; on ne reprend jamais la **marque** (couleurs signature, logo, illustrations, textes).

1. Depuis `recon.md`, liste les composants récurrents (barre de navigation, carte, liste, créneau horaire, modale, bouton principal…).
2. Définis les tokens dans `app/globals.css` (variables CSS) et `tailwind.config.ts` : 1 couleur d'accent (différente de l'original), neutres, rouge d'erreur, rayon, ombres, échelle typographique, espacements 4/8 px. Mode sombre inclus.
3. Crée les composants de base dans `components/ui/` (shadcn) et une page `/design` qui les affiche tous.
4. Vérifie le contraste AA de chaque couple texte/fond.

Sortie : la page `/design` qui tourne + `replica/design.md` (tokens et règles).
