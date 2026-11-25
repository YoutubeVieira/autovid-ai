---
name: replica-reviews
description: "Lit les avis publics de l'app clonée (App Store, Google Play, G2, Trustpilot, Reddit) et en tire les problèmes que ton clone doit résoudre. C'est « l'entrepreneur » de Replica. Utiliser pour « lis les avis », « ce que les utilisateurs détestent », « pesquisa », « replica-reviews »."
---

# /replica-reviews — l'entrepreneur

Le clone ne gagne pas en étant identique : il gagne en réglant ce que les utilisateurs de l'original détestent.

## Collecte
- Sources : App Store, Google Play, G2, Capterra, Trustpilot, Reddit. Utilise la recherche web si disponible, sinon demande à l'utilisateur de coller les avis.
- Vise **100+ avis**, en priorité les 1 à 3 étoiles des 12 derniers mois. Affiche le compteur : `140 avis lus`.

## Analyse
1. Regroupe les plaintes par **problème** (pas par mot-clé) : ex. « fuseau horaire confus », « pas de rappel SMS », « prix qui augmente ».
2. Pour chaque problème : nombre d'avis, gravité (fait partir l'utilisateur ?), **une citation réelle avec son lien**.
3. Repère aussi ce qu'ils **aiment** : à ne surtout pas casser.

## Livrable : `replica/reviews.md`
| # | Problème | Avis | Gravité | Citation (lien) | Réponse dans notre app |
|---|----------|------|---------|-----------------|------------------------|

Puis : « Notre angle : <la promesse qui répond aux 3 premiers problèmes> ». Cet angle alimente `/replica-brand` et la page d'accueil. Ajoute les réponses en *Must* dans `replica/recon.md`.
